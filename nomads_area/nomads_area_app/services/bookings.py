import uuid
from decimal import Decimal

from django.db import transaction

from ..exceptions import InsufficientSpotsError
from ..models import Booking, TourDate
from .common import (
    _acquire_fingerprint_lock,
    _fingerprint,
    _normalize_text,
    _recent_duplicate,
    quantize_money,
)


def calculate_booking_price(tour, total_people, price_tier=None):
    if tour.tour_type == "private" and price_tier:
        price_per_person = Decimal(price_tier.price_per_person)
    else:
        price_per_person = Decimal(tour.price)
    total_price = quantize_money(price_per_person * total_people)
    return {
        "price_per_person": quantize_money(price_per_person),
        "total_price": total_price,
    }

def _create_booking_db(validated_data, price_data, tour_date):
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
        currency=data["tour"].currency,
        status=Booking.STATUS_PENDING,
        **data,
    )
    if extra_services:
        booking.extra_services.set(extra_services)
    return booking

def create_booking_service(validated_data, price_tier=None, tour_date=None):
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
            return existing, True
        booking = _create_booking_db(validated_data, price_data, tour_date)
        return booking, False
