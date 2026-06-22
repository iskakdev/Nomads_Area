import hashlib
import json
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import connection
from django.utils import timezone


DEDUP_WINDOW_MINUTES = 5


def quantize_money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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
