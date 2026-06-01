import hashlib
import hmac
import logging
from decimal import Decimal
import requests
from django.conf import settings
logger = logging.getLogger(__name__)

class PaymentProviderError(Exception): pass
class PaymentVerificationError(PaymentProviderError): pass

class FinikPayClient:
    provider_name = "finikpay"
    def __init__(self):
        self.api_key = getattr(settings, "FINIKPAY_API_KEY", "")
        self.secret_key = getattr(settings, "FINIKPAY_SECRET_KEY", "")
        self.base_url = getattr(settings, "FINIKPAY_BASE_URL", "").rstrip("/")
        self.return_url = getattr(settings, "FINIKPAY_RETURN_URL", "")
        self.cancel_url = getattr(settings, "FINIKPAY_CANCEL_URL", "")
        self.webhook_secret = getattr(settings, "FINIKPAY_WEBHOOK_SECRET", "")

    def create_payment(self, payment):
        if not self.base_url or not self.api_key:
            logger.warning("FinikPay not configured. Fallback used.")
            return {"provider_payment_id": f"local-{payment.id}", "payment_url": f"/payments/{payment.id}/pending/"}
        payload = {
            "amount": str(Decimal(payment.amount)), "currency": payment.currency,
            "description": f"Nomads Area booking #{payment.booking_id}", "reference_id": str(payment.id),
            "return_url": self.return_url, "cancel_url": self.cancel_url
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(f"{self.base_url}/payments", json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("FinikPay create failed: %s", exc)
            raise PaymentProviderError("Не удалось создать платёж.") from exc
        data = resp.json()
        return {"provider_payment_id": data.get("id", ""), "payment_url": data.get("payment_url", "")}

    def verify_webhook_signature(self, raw_body, signature):
        if not self.webhook_secret:
            logger.warning("Webhook secret missing.")
            return False
        expected = hmac.new(self.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature or "")

    def parse_webhook(self, payload):
        ref = payload.get("reference_id") or payload.get("metadata", {}).get("payment_id")
        if not ref: raise PaymentVerificationError("Missing reference_id.")
        return {
            "payment_id": int(ref),
            "provider_payment_id": str(payload.get("id") or payload.get("payment_id") or ""),
            "status": str(payload.get("status") or "").lower()
        }

def get_payment_provider():
    return FinikPayClient()
