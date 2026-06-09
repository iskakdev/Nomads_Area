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
        f"<b>Людей:</b> {booking.number_of_people}\n"
        f"<b>Сумма:</b> {booking.total_price} {booking.currency}\n"
        f"<b>Предоплата:</b> {booking.prepayment_amount} {booking.currency}\n"
        f"<b>Статус:</b> {clean(booking.status)}"
    )
    if booking.tour_date:
        text += f"\n<b>Дата:</b> {booking.tour_date.start_date} - {booking.tour_date.end_date}"
    if booking.preferred_start_date and booking.preferred_end_date:
        text += f"\n<b>Желаемые даты:</b> {booking.preferred_start_date} - {booking.preferred_end_date}"
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
    text = f"📝 <b>Лид из квиза #{lead.id}</b>\n\n<b>Имя:</b> {clean(lead.customer_name)}\n<b>Контакт:</b> {clean(lead.customer_contact)}"
    send_telegram_task.delay(text)
    send_email_task.delay(f"Лид квиза #{lead.id}", f"Имя: {lead.customer_name}\nКонтакт: {lead.customer_contact}\nОтветы: {lead.answers_data}")


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