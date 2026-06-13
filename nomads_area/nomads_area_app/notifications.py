import html
from .tasks import send_email_task, send_telegram_task


def clean(v):
    return html.escape(str(v)) if v is not None else ""


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
    if booking.comment:
        text += f"\n<b>Комментарий:</b> {clean(booking.comment)}"

    send_telegram_task.delay(text)
    send_email_task.delay(f"Новая бронь #{booking.id}", text.replace("<b>", "").replace("</b>", ""))


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
    send_telegram_task.delay(text)
    send_email_task.delay(f"Оплата брони #{b.id}", text.replace("<b>", "").replace("</b>", ""))


def send_quiz_notification(lead):
    def quiz_label(key):
        k = str(key).lower()

        if "формат путешествия" in k or "формат тура" in k:
            return "Формат"
        if "регион" in k or "страна" in k or "куда" in k:
            return "Регион"
        if "бюджет" in k:
            return "Бюджет"
        if "сколько дней" in k or "дней" in k:
            return "Длительность"
        if "вид активности" in k or "активности" in k:
            return "Интерес"
        if "когда" in k or "планируете" in k:
            return "Срок поездки"
        if "человек" in k or "сколько человек" in k:
            return "Людей"
        if "пожелания" in k:
            return "Пожелания"
        if "комфортность" in k or "проживания" in k:
            return "Комфорт"
        if "рекомендации" in k or "получить" in k:
            return "Связь"

        return str(key)

    answers = lead.answers_data or {}

    text = (
        f"📝 <b>Лид из квиза #{lead.id}</b>\n\n"
        f"👤 <b>Клиент</b>\n"
        f"<b>Имя:</b> {clean(lead.customer_name) if lead.customer_name else 'Не указано'}\n"
        f"<b>Контакт:</b> {clean(lead.customer_contact)}"
    )

    if answers:
        text += "\n\n🧭 <b>Запрос</b>"
        for key, value in answers.items():
            label = quiz_label(key)
            text += f"\n<b>{clean(label)}:</b> {clean(str(value))}"
    else:
        text += "\n\n🧭 <b>Запрос:</b> Не указан"

    send_telegram_task.delay(text)

    email_text = text.replace("<b>", "").replace("</b>", "")
    send_email_task.delay(f"Лид квиза #{lead.id}", email_text)


def send_transport_notification(tr):
    v, r = tr.vehicle, tr.vehicle.route
    text = (
        f"🚘 <b>Трансфер #{tr.id}</b>\n\n"
        f"<b>Маршрут:</b> {clean(r.departure_point)} → {clean(r.arrival_point)}\n"
        f"<b>Авто:</b> {clean(v.get_category_display())}\n"
        f"<b>Клиент:</b> {clean(tr.customer_name)}\n"
        f"<b>Телефон:</b> {clean(tr.customer_phone)}\n"
        f"<b>Цена:</b> {tr.total_price}"
    )
    if tr.comment:
        text += f"\n<b>Комментарий:</b> {clean(tr.comment)}"
    send_telegram_task.delay(text)
    send_email_task.delay(f"Трансфер #{tr.id}", text.replace("<b>", "").replace("</b>", ""))


def send_contact_notification(cr):
    text = (
        f"📩 <b>Заявка #{cr.id}</b>\n\n"
        f"<b>Имя:</b> {clean(cr.name)}\n"
        f"<b>Контакт:</b> {clean(cr.phone_or_email)}\n"
        f"<b>Тема:</b> {clean(cr.subject)}\n"
        f"<b>Источник:</b> {clean(cr.source)}\n"
        f"<b>Сообщение:</b> {clean(cr.message)}"
    )
    send_telegram_task.delay(text)
    send_email_task.delay(f"Заявка #{cr.id}", text.replace("<b>", "").replace("</b>", ""))
