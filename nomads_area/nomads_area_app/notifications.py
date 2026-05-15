import logging
from .tasks import send_email_task, send_telegram_task

logger = logging.getLogger(__name__)

# ========================
# BOOKING
# ========================

def send_booking_notification(booking):
    if booking.tour_date:
        date_display = f"{booking.tour_date.start_date} - {booking.tour_date.end_date}"
    else:
        date_display = str(booking.preferred_start_date or "")
        if booking.preferred_end_date:
            date_display += f" - {booking.preferred_end_date}"

    telegram_text = (
        f"<b>Новое бронирование!</b>\n\n"
        f"<b>Тур:</b> {booking.tour.title}\n"
        f"<b>Тип:</b> {booking.tour.get_tour_type_display()}\n"
        f"<b>Дата:</b> {date_display}\n\n"
        f"<b>Имя:</b> {booking.customer_name}\n"
        f"<b>Контакт:</b> {booking.customer_contact}\n"
        f"<b>Людей:</b> {booking.number_of_people} "
        f"(взрослых: {booking.adults}, детей: {booking.children})\n"
    )
    if booking.people_details:
        telegram_text += f"<b>Состав:</b> {booking.people_details}\n"
    telegram_text += f"\n<b>Стоимость:</b> {booking.total_price} {booking.tour.currency}\n"
    if booking.comment:
        telegram_text += f"\n<b>Комментарий:</b> {booking.comment}\n"

    email_body = (
        f"Новое бронирование!\n\n"
        f"Тур: {booking.tour.title}\n"
        f"Тип: {booking.tour.get_tour_type_display()}\n"
        f"Дата: {date_display}\n\n"
        f"Имя: {booking.customer_name}\n"
        f"Контакт: {booking.customer_contact}\n"
        f"Людей: {booking.number_of_people} "
        f"(взрослых: {booking.adults}, детей: {booking.children})\n"
    )
    if booking.people_details:
        email_body += f"Состав: {booking.people_details}\n"
    email_body += f"\nСтоимость: {booking.total_price} {booking.tour.currency}\n"
    if booking.comment:
        email_body += f"\nКомментарий: {booking.comment}\n"

    send_telegram_task.delay(telegram_text)
    send_email_task.delay(f"Бронирование: {booking.tour.title}", email_body)

# ========================
# QUIZ
# ========================

def send_quiz_notification(quiz_lead):
    telegram_text = "<b>Новая заявка с квиза!</b>\n\n"
    email_body = "Новая заявка с квиза!\n\n"

    if quiz_lead.name:
        telegram_text += f"<b>Имя:</b> {quiz_lead.name}\n"
        email_body += f"Имя: {quiz_lead.name}\n"
    if quiz_lead.phone_or_telegram:
        telegram_text += f"<b>Контакт:</b> {quiz_lead.phone_or_telegram}\n"
        email_body += f"Контакт: {quiz_lead.phone_or_telegram}\n"

    telegram_text += "\n<b>Ответы:</b>\n"
    email_body += "\nОтветы:\n"

    if isinstance(quiz_lead.answers, dict):
        for index, (question, answer) in enumerate(quiz_lead.answers.items(), 1):
            formatted = ", ".join(answer) if isinstance(answer, list) else str(answer)
            telegram_text += f"{index}. <b>{question}</b>\n   -> {formatted}\n"
            email_body += f"{index}. {question}\n   -> {formatted}\n"

    send_telegram_task.delay(telegram_text)
    send_email_task.delay("Заявка с квиза", email_body)

# ========================
# TRANSPORT
# ========================

def send_transport_notification(transport_request):
    vehicle = transport_request.vehicle
    route = vehicle.route

    telegram_text = (
        f"<b>Новый запрос на трансфер!</b>\n\n"
        f"<b>Маршрут:</b> {route.departure_point} -> {route.arrival_point}\n"
        f"<b>Транспорт:</b> {vehicle.get_category_display()}\n"
        f"<b>Телефон:</b> {transport_request.customer_phone}\n"
        f"<b>Пассажиров:</b> {transport_request.passengers}\n"
        f"<b>Стоимость:</b> {transport_request.total_price} USD\n"
    )
    email_body = (
        f"Новый запрос на трансфер!\n\n"
        f"Маршрут: {route.departure_point} -> {route.arrival_point}\n"
        f"Транспорт: {vehicle.get_category_display()}\n"
        f"Телефон: {transport_request.customer_phone}\n"
        f"Пассажиров: {transport_request.passengers}\n"
        f"Стоимость: {transport_request.total_price} USD\n"
    )

    if transport_request.customer_name:
        telegram_text += f"<b>Имя:</b> {transport_request.customer_name}\n"
        email_body += f"Имя: {transport_request.customer_name}\n"
    if transport_request.comment:
        telegram_text += f"<b>Комментарий:</b> {transport_request.comment}\n"
        email_body += f"Комментарий: {transport_request.comment}\n"

    send_telegram_task.delay(telegram_text)
    send_email_task.delay("Запрос на трансфер", email_body)

# ========================
# CONTACT
# ========================

def send_contact_notification(contact_request):
    telegram_text = (
        f"<b>Новая контактная заявка!</b>\n\n"
        f"<b>Имя:</b> {contact_request.name}\n"
        f"<b>Контакт:</b> {contact_request.phone_or_email}\n"
        f"<b>Источник:</b> {contact_request.source or 'не указан'}\n"
        f"<b>Тема:</b> {contact_request.subject or 'не указана'}\n"
        f"\n<b>Сообщение:</b>\n{contact_request.message}\n"
    )
    email_body = (
        f"Новая контактная заявка!\n\n"
        f"Имя: {contact_request.name}\n"
        f"Контакт: {contact_request.phone_or_email}\n"
        f"Источник: {contact_request.source or 'не указан'}\n"
        f"Тема: {contact_request.subject or 'не указана'}\n"
        f"\nСообщение:\n{contact_request.message}\n"
    )

    email_subject = f"Контакт: {contact_request.subject or contact_request.name}"

    send_telegram_task.delay(telegram_text)
    send_email_task.delay(email_subject, email_body)