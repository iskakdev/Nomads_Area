import hashlib
import json
import logging
import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.db import connection, transaction
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


def _normalize_text(value):
    return " ".join(str(value or "").strip().lower().split())


def _fingerprint(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _acquire_fingerprint_lock(fingerprint):
    """Serialize equal submissions across all Gunicorn workers."""
    if connection.vendor != "postgresql":
        return
    lock_id = int(fingerprint[:16], 16)
    if lock_id >= 2**63:
        lock_id -= 2**64
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])


def _recent_duplicate(model, fingerprint):
    window = timezone.now() - timedelta(minutes=DEDUP_WINDOW_MINUTES)
    return model.objects.filter(
        request_fingerprint=fingerprint,
        created_at__gte=window,
    ).order_by("-created_at").first()


def _create_booking_and_payment_db(validated_data, price_data, tour_date):
    """Только БД-операции. Вызывается строго внутри transaction.atomic()."""
    locked_tour_date = None
    if tour_date is not None:
        locked_tour_date = TourDate.objects.select_for_update().get(pk=tour_date.pk)
        total_people = validated_data["adults"] + validated_data.get("children", 0)
        if total_people > locked_tour_date.available_spots:
            raise InsufficientSpotsError(available=locked_tour_date.available_spots)

    # Убираем tour_date из validated_data — передаём явно через locked_tour_date
    extra_services = validated_data.pop("extra_services", [])
    data = {k: v for k, v in validated_data.items() if k != "tour_date"}

    booking = Booking.objects.create(
        tour_date=locked_tour_date,
        price_per_person=price_data["price_per_person"],
        total_price=price_data["total_price"],
        prepayment_amount=price_data["prepayment_amount"],
        currency=data["tour"].currency,
        status=Booking.STATUS_PENDING,
        **data,
    )
    if extra_services:
        booking.extra_services.set(extra_services)

    payment = Payment.objects.create(
        booking=booking,
        provider=Payment.PROVIDER_FINIKPAY,
        amount=booking.prepayment_amount,
        currency=booking.currency,
        status=Payment.STATUS_PENDING,
    )
    return booking, payment


def create_booking_with_payment_service(validated_data, price_tier=None, tour_date=None):
    validated_data = validated_data.copy()
    tour = validated_data["tour"]
    total_people = validated_data["adults"] + validated_data.get("children", 0)
    price_data = calculate_booking_price(tour=tour, total_people=total_people, price_tier=price_tier)
    extra_service_ids = sorted(service.pk for service in validated_data.get("extra_services", []))
    fingerprint = _fingerprint({
        "tour": tour.pk,
        "tour_date": tour_date.pk if tour_date else None,
        "preferred_start_date": validated_data.get("preferred_start_date"),
        "preferred_end_date": validated_data.get("preferred_end_date"),
        "customer_name": _normalize_text(validated_data.get("customer_name")),
        "customer_contact": _normalize_text(validated_data.get("customer_contact")),
        "adults": validated_data["adults"],
        "children": validated_data.get("children", 0),
        "comment": _normalize_text(validated_data.get("comment")),
        "extra_services": extra_service_ids,
    })
    validated_data["customer_contact"] = str(validated_data["customer_contact"]).strip()
    validated_data["request_fingerprint"] = fingerprint
    validated_data["dedup_hash"] = _fingerprint({"fingerprint": fingerprint, "nonce": uuid.uuid4().hex})

    # Шаг 1: только БД, никакого IO
    with transaction.atomic():
        _acquire_fingerprint_lock(fingerprint)
        existing = _recent_duplicate(Booking, fingerprint)
        if existing:
            return existing, existing.payments.order_by("-created_at").first(), True
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
        payment, _ = payment.mark_failed()

    return booking, payment, False


def confirm_payment_service(payment, provider_payload=None):
    return payment.mark_paid_and_confirm_booking(provider_payload=provider_payload)


def handle_payment_webhook_service(payload):
    provider = get_payment_provider()
    parsed = provider.parse_webhook(payload)
    payment = Payment.objects.select_related("booking", "booking__tour", "booking__tour_date").get(pk=parsed["payment_id"])

    if (
        parsed["provider_payment_id"]
        and payment.provider_payment_id
        and payment.provider_payment_id != parsed["provider_payment_id"]
    ):
        raise serializers.ValidationError("Provider payment ID mismatch.")
    if parsed["provider_payment_id"] and not payment.provider_payment_id:
        payment.provider_payment_id = parsed["provider_payment_id"]
        payment.save(update_fields=["provider_payment_id", "updated_at"])

    if parsed["status"] in {"paid", "success", "succeeded", "confirmed"}:
        payment, changed = confirm_payment_service(payment=payment, provider_payload=payload)
        return {"payment": payment, "changed": changed}
    if parsed["status"] in {"failed", "cancelled", "canceled", "error"}:
        payment, changed = payment.mark_failed(provider_payload=payload)
        return {"payment": payment, "changed": changed}
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


def create_quiz_lead_service(validated_data):
    validated_data = validated_data.copy()
    validated_data["customer_contact"] = str(validated_data["customer_contact"]).strip()
    fingerprint = _fingerprint({
        "customer_name": _normalize_text(validated_data.get("customer_name")),
        "customer_contact": _normalize_text(validated_data["customer_contact"]),
        "answers_data": validated_data.get("answers_data") or {},
    })
    with transaction.atomic():
        _acquire_fingerprint_lock(fingerprint)
        duplicate = _recent_duplicate(QuizLead, fingerprint)
        if duplicate:
            return duplicate, True
        return QuizLead.objects.create(request_fingerprint=fingerprint, **validated_data), False


def create_transport_request_service(validated_data):
    validated_data = validated_data.copy()
    validated_data["customer_phone"] = str(validated_data["customer_phone"]).strip()
    fingerprint = _fingerprint({
        "vehicle": validated_data["vehicle"].pk,
        "customer_name": _normalize_text(validated_data.get("customer_name")),
        "customer_phone": _normalize_text(validated_data["customer_phone"]),
        "passengers": validated_data.get("passengers", 1),
        "bags": validated_data.get("bags", 0),
        "comment": _normalize_text(validated_data.get("comment")),
    })
    with transaction.atomic():
        _acquire_fingerprint_lock(fingerprint)
        duplicate = _recent_duplicate(TransportRequest, fingerprint)
        if duplicate:
            return duplicate, True
        return TransportRequest.objects.create(
            request_fingerprint=fingerprint,
            total_price=validated_data["vehicle"].price,
            status="pending",
            **validated_data,
        ), False


def create_contact_request_service(validated_data):
    validated_data = validated_data.copy()
    validated_data["phone_or_email"] = str(validated_data["phone_or_email"]).strip()
    fingerprint = _fingerprint({
        "name": _normalize_text(validated_data.get("name")),
        "phone_or_email": _normalize_text(validated_data["phone_or_email"]),
        "subject": _normalize_text(validated_data.get("subject")),
        "message": _normalize_text(validated_data.get("message")),
        "source": _normalize_text(validated_data.get("source")),
    })
    with transaction.atomic():
        _acquire_fingerprint_lock(fingerprint)
        duplicate = _recent_duplicate(ContactRequest, fingerprint)
        if duplicate:
            return duplicate, True
        return ContactRequest.objects.create(request_fingerprint=fingerprint, **validated_data), False
