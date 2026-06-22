from django.db import transaction

from ..models import ContactRequest
from .common import (
    _acquire_fingerprint_lock,
    _fingerprint,
    _normalize_text,
    _recent_duplicate,
)


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
