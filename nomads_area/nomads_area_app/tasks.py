import logging
import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_telegram_task(self, text):
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Telegram error: %s", e)
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_task(self, subject, body, to_email=None):
    recipient = to_email or getattr(settings, "ADMIN_EMAIL", "")
    if not recipient or not getattr(settings, "EMAIL_HOST_USER", ""): return
    try:
        send_mail(subject=subject, message=body, from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[recipient], fail_silently=False)
    except Exception as e:
        logger.exception("Email error: %s", e)
        raise self.retry(exc=e)
