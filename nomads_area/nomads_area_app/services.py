import hashlib
import logging
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .exceptions import InsufficientSpotsError
from .models import Booking, ContactRequest, Payment, QuizLead, QuizQuestion, TourDate, TransportRequest
from .payment_providers import get_payment_provider

logger = logging.getLogger(__name__)
DEDUP_WINDOW_MINUTES = 5
PREPAYMENT_PERCENT = Decimal("0.30")


def quantize_money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_booking_price(tour, total_people, price_tier=None):
    if tour.tour_type == "private" and price_tier:
        price_per_person = Decimal(price_tier.price_per_person)
    else:
        price_per_person = Decimal(tour.price)
    total_price = quantize_money(price_per_person * total_people)
    return {
        "price_per_person": quantize_money(price_per_person),
        "total_price": total_price,
        "prepayment_amount": quantize_money(total_price * PREPAYMENT_PERCENT),
    }


def _create_booking_and_payment_db(validated_data, price_data, tour_date):
    """Только БД-операции. Вызывается строго внутри transaction.atomic()."""
    locked_tour_date = None
    if tour_date is not None:
        locked_tour_date = TourDate.objects.select_for_update().get(pk=tour_date.pk)
        total_people = validated_data["adults"] + validated_data.get("children", 0)
        if total_people > locked_tour_date.available_spots:
            raise InsufficientSpotsError(available=locked_tour_date.available_spots)

    booking = Booking.objects.create(
        tour_date=locked_tour_date,
        price_per_person=price_data["price_per_person"],
        total_price=price_data["total_price"],
        prepayment_amount=price_data["prepayment_amount"],
        currency=validated_data["tour"].currency,
        status=Booking.STATUS_PENDING,
        **validated_data,
    )
    payment = Payment.objects.create(
        booking=booking,
        provider=Payment.PROVIDER_FINIKPAY,
        amount=booking.prepayment_amount,
        currency=booking.currency,
        status=Payment.STATUS_PENDING,
    )
    return booking, payment


def create_booking_with_payment_service(validated_data, price_tier=None, tour_date=None):
    tour = validated_data["tour"]
    customer_contact = validated_data["customer_contact"]
    total_people = validated_data["adults"] + validated_data.get("children", 0)
    price_data = calculate_booking_price(tour=tour, total_people=total_people, price_tier=price_tier)
    created_at = timezone.now()

    dedup_key = f"{tour.id}:{customer_contact.lower().strip()}:{created_at.strftime('%Y-%m-%d-%H')}"
    dedup_hash = hashlib.sha256(dedup_key.encode()).hexdigest()[:64]

    # Шаг 1: только БД, никакого IO
    with transaction.atomic():
        try:
            existing = Booking.objects.select_for_update().get(dedup_hash=dedup_hash)
            return existing, existing.payments.order_by("-created_at").first(), True
        except Booking.DoesNotExist:
            booking, payment = _create_booking_and_payment_db(validated_data, price_data, tour_date)

    # Шаг 2: HTTP-запрос к провайдеру строго вне транзакции
    try:
        provider = get_payment_provider()
        data = provider.create_payment(payment)
        payment.provider_payment_id = data.get("provider_payment_id", "")
        payment.payment_url = data.get("payment_url", "")
        payment.save(update_fields=["provider_payment_id", "payment_url", "updated_at"])
    except Exception as e:
        logger.exception("Payment provider error: %s", e)
        payment.mark_failed()

    return booking, payment, False


def confirm_payment_service(payment, provider_payload=None):
    return payment.mark_paid_and_confirm_booking(provider_payload=provider_payload)


def handle_payment_webhook_service(payload):
    provider = get_payment_provider()
    parsed = provider.parse_webhook(payload)
    payment = Payment.objects.select_related("booking", "booking__tour", "booking__tour_date").get(pk=parsed["payment_id"])

    if parsed["provider_payment_id"] and payment.provider_payment_id != parsed["provider_payment_id"]:
        payment.provider_payment_id = parsed["provider_payment_id"]
        payment.save(update_fields=["provider_payment_id", "updated_at"])

    if parsed["status"] in {"paid", "success", "succeeded", "confirmed"}:
        payment, changed = confirm_payment_service(payment=payment, provider_payload=payload)
        return {"payment": payment, "changed": changed}
    if parsed["status"] in {"failed", "cancelled", "canceled", "error"}:
        payment.mark_failed(provider_payload=payload)
        return {"payment": payment, "changed": True}
    return {"payment": payment, "changed": False}


def update_quiz_progress_service(progress, validated_data):
    question_id = validated_data["question_id"]
    text_answer = validated_data.get("text_answer", "")
    selected_options = validated_data.get("selected_options", [])

    try:
        question = QuizQuestion.objects.prefetch_related("options").get(pk=question_id)
    except QuizQuestion.DoesNotExist as exc:
        raise serializers.ValidationError({"question_id": "Вопрос не найден."}) from exc

    answers = progress.answers_data or {}
    if question.question_type == "text":
        answers[str(question_id)] = {"question": question.question_text, "answer": text_answer}
        next_opt = question.options.filter(next_question__isnull=False).first()
        next_id = next_opt.next_question_id if next_opt else None
    else:
        selected_objects = question.options.filter(id__in=selected_options)
        answers[str(question_id)] = {"question": question.question_text, "answer": [o.option_text for o in selected_objects]}
        next_id = next((o.next_question_id for o in selected_objects if o.next_question_id), None)

    progress.answers_data = answers
    if next_id:
        progress.current_question_index = next_id
    else:
        nxt = QuizQuestion.objects.filter(is_active=True, order__gt=question.order).order_by("order").first()
        progress.current_question_index = nxt.id if nxt else progress.current_question_index
        progress.is_completed = not nxt
    progress.save(update_fields=["answers_data", "current_question_index", "is_completed", "updated_at"])
    return progress


def _find_duplicate(model, **kwargs):
    window = timezone.now() - timedelta(minutes=DEDUP_WINDOW_MINUTES)
    kwargs["created_at__gte"] = window
    return model.objects.filter(**kwargs).first()


def create_quiz_lead_service(validated_data):
    dup = _find_duplicate(QuizLead, customer_contact=validated_data["customer_contact"])
    return (dup, True) if dup else (QuizLead.objects.create(**validated_data), False)


def create_transport_request_service(validated_data):
    dup = _find_duplicate(TransportRequest, vehicle=validated_data["vehicle"], customer_phone=validated_data["customer_phone"])
    return (dup, True) if dup else (TransportRequest.objects.create(total_price=validated_data["vehicle"].price, status="pending", **validated_data), False)


def create_contact_request_service(validated_data):
    dup = _find_duplicate(ContactRequest, phone_or_email=validated_data["phone_or_email"], message=validated_data["message"])
    return (dup, True) if dup else (ContactRequest.objects.create(**validated_data), False)
