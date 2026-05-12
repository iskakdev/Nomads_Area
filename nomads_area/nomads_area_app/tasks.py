import logging
import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

# ========================
# TELEGRAM TASK
# ========================

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_telegram_task(self, text):
    """Отправка сообщения в Telegram через Celery."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

    if not bot_token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Ошибка отправки в Telegram: %s", e)
        raise self.retry(exc=e)

# ========================
# EMAIL TASK
# ========================

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(self, subject, body, to_email=None):
    """Отправка письма через Celery."""
    recipient = to_email or getattr(settings, "ADMIN_EMAIL", None)

    if not recipient:
        return

    if not settings.EMAIL_HOST_USER:
        return

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception as e:
        logger.exception("Ошибка отправки Email: %s", e)
        raise self.retry(exc=e)