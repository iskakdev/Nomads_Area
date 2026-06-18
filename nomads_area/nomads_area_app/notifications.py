import html
import logging
from .tasks import send_email_task, send_telegram_task

logger = logging.getLogger(__name__)


def clean(v):
    return html.escape(str(v)) if v is not None else ""


def enqueue_task_safely(task, *args):
    try:
        return task.delay(*args)
    except Exception as exc:
        # Notification delivery must never break a successfully saved lead/booking.
        logger.exception("Failed to enqueue notification task %s: %s", getattr(task, "name", task), exc)
        return None


def send_booking_notification(booking):
    text = (
        f"🧭 <b>Новая бронь #{booking.id}</b>\n\n"
        f"<b>Тур:</b> {clean(booking.tour.title)}\n"
        f"<b>Тип тура:</b> {clean(booking.tour.get_tour_type_display())}\n"
        f"<b>Клиент:</b> {clean(booking.customer_name)}\n"
        f"<b>Контакт:</b> {clean(booking.customer_contact)}\n"
        f"<b>Взрослые:</b> {booking.adults}\n"
        f"<b>Дети:</b> {booking.children}\n"
        f"<b>Всего людей:</b> {booking.number_of_people}\n"
        f"<b>Сумма:</b> {booking.total_price} {booking.currency}\n"
        f"<b>Предоплата:</b> {booking.prepayment_amount} {booking.currency}\n"
        f"<b>Статус:</b> {clean(booking.status)}"
    )
    if booking.tour_date:
        text += f"\n<b>Дата:</b> {booking.tour_date.start_date.strftime('%d.%m.%Y')} - {booking.tour_date.end_date.strftime('%d.%m.%Y')}"
    if booking.preferred_start_date and booking.preferred_end_date:
        text += f"\n<b>Желаемые даты:</b> {booking.preferred_start_date.strftime('%d.%m.%Y')} - {booking.preferred_end_date.strftime('%d.%m.%Y')}"
    selected_services = list(booking.extra_services.all())
    if selected_services:
        services_text = "\n".join(
            f"• {clean(service.title)} — {service.price} {clean(service.currency)}"
            for service in selected_services
        )
        text += f"\n<b>Доп. услуги:</b>\n{services_text}"
    if booking.comment:
        text += f"\n<b>Комментарий:</b> {clean(booking.comment)}"

    enqueue_task_safely(send_telegram_task, text)
    enqueue_task_safely(send_email_task, f"Новая бронь #{booking.id}", text.replace("<b>", "").replace("</b>", ""))


def send_payment_success_notification(payment):
    b = payment.booking
    text = (
        f"✅ <b>Оплата получена</b>\n\n"
        f"<b>Платёж:</b> #{payment.id}\n"
        f"<b>Бронь:</b> #{b.id}\n"
        f"<b>Тур:</b> {clean(b.tour.title)}\n"
        f"<b>Клиент:</b> {clean(b.customer_name)}\n"
        f"<b>Сумма:</b> {payment.amount} {payment.currency}"
    )
    enqueue_task_safely(send_telegram_task, text)
    enqueue_task_safely(send_email_task, f"Оплата брони #{b.id}", text.replace("<b>", "").replace("</b>", ""))


def send_quiz_notification(lead):
    answers = lead.answers_data or {}

    def detect_answers_language():
        questions = " ".join(str(key).lower() for key in answers)

        if any("\u0400" <= char <= "\u04ff" for char in questions):
            return "ru"
        if any(marker in questions for marker in ("¿", "cuánt", "presupuesto", "viaje", "personas")):
            return "es"
        if any(marker in questions for marker in ("quel ", "quelle ", "combien", "souhaitez", "voyage")):
            return "fr"
        if any(marker in questions for marker in ("welche", "welcher", "wie viele", "reise", "unterkunft")):
            return "de"
        return "en"

    language = detect_answers_language()
    labels = {
        "ru": {
            "format": "Формат",
            "region": "Регион",
            "budget": "Бюджет",
            "duration": "Продолжительность",
            "activity": "Активность",
            "travel_date": "Дата поездки",
            "people": "Количество людей",
            "requests": "Пожелания",
            "comfort": "Комфорт",
            "contact": "Способ связи",
        },
        "en": {
            "format": "Format",
            "region": "Region",
            "budget": "Budget",
            "duration": "Duration",
            "activity": "Activity",
            "travel_date": "Travel date",
            "people": "People",
            "requests": "Requests",
            "comfort": "Comfort",
            "contact": "Contact",
        },
        "es": {
            "format": "Formato",
            "region": "Región",
            "budget": "Presupuesto",
            "duration": "Duración",
            "activity": "Actividad",
            "travel_date": "Fecha del viaje",
            "people": "Personas",
            "requests": "Solicitudes",
            "comfort": "Comodidad",
            "contact": "Contacto",
        },
        "fr": {
            "format": "Format",
            "region": "Région",
            "budget": "Budget",
            "duration": "Durée",
            "activity": "Activité",
            "travel_date": "Date du voyage",
            "people": "Voyageurs",
            "requests": "Demandes",
            "comfort": "Confort",
            "contact": "Contact",
        },
        "de": {
            "format": "Reiseformat",
            "region": "Region",
            "budget": "Budget",
            "duration": "Dauer",
            "activity": "Aktivität",
            "travel_date": "Reisezeit",
            "people": "Personen",
            "requests": "Wünsche",
            "comfort": "Komfort",
            "contact": "Kontakt",
        },
    }

    categories = (
        ("format", ("формат", "type of travel", "travel do you prefer", "tipo de viaje", "type de voyage", "reiseart", "art von reise")),
        ("region", ("регион", "страна", "куда", "region", "central asia", "región", "région", "zentralasien")),
        ("budget", ("бюджет", "budget", "presupuesto")),
        ("duration", ("сколько дней", "дней", "how many days", "days do you have", "cuántos días", "combien de jours", "wie viele tage")),
        ("activity", ("актив", "интерес", "activity", "actividad", "activité", "aktivität")),
        ("travel_date", ("когда", "планируете", "planning to travel", "cuándo", "quand", "wann")),
        ("people", ("человек", "people", "personas", "personnes", "personen")),
        ("requests", ("пожелания", "special requests", "solicitudes especiales", "demandes spéciales", "besondere wünsche")),
        ("comfort", ("комфорт", "прожив", "comfort", "alojamiento", "hébergement", "unterkunft")),
        ("contact", ("рекомендации", "получить", "recommendations", "recibir recomendaciones", "recevoir", "empfehlungen")),
    )

    def quiz_label(key):
        normalized_key = str(key).strip().lower()
        for category, markers in categories:
            if any(marker in normalized_key for marker in markers):
                return labels[language][category]
        return str(key)

    text = (
        f"📝 <b>Лид из квиза #{lead.id}</b>\n\n"
        f"👤 <b>Клиент</b>\n"
        f"<b>Имя:</b> {clean(lead.customer_name) if lead.customer_name else 'Не указано'}\n"
        f"<b>Контакт:</b> {clean(lead.customer_contact)}"
    )

    if answers:
        text += "\n\n🧭 <b>Запрос</b>"
        for key, value in answers.items():
            text += f"\n<b>{clean(quiz_label(key))}:</b> {clean(str(value))}"
    else:
        text += "\n\n🧭 <b>Запрос:</b> Не указан"

    enqueue_task_safely(send_telegram_task, text)

    email_text = text.replace("<b>", "").replace("</b>", "")
    enqueue_task_safely(send_email_task, f"Лид квиза #{lead.id}", email_text)


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
