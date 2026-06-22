from ..tasks import send_email_task, send_telegram_task
from .common import clean, enqueue_task_safely


def send_contact_notification(cr):
    text = (
        f"📩 <b>Заявка #{cr.id}</b>\n\n"
        f"<b>Имя:</b> {clean(cr.name)}\n"
        f"<b>Контакт:</b> {clean(cr.phone_or_email)}\n"
        f"<b>Тема:</b> {clean(cr.subject)}\n"
        f"<b>Источник:</b> {clean(cr.source)}\n"
        f"<b>Сообщение:</b> {clean(cr.message)}"
    )
    enqueue_task_safely(send_telegram_task, text)
    enqueue_task_safely(send_email_task, f"Заявка #{cr.id}", text.replace("<b>", "").replace("</b>", ""))
