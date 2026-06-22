from ..tasks import send_email_task, send_telegram_task
from .common import clean, enqueue_task_safely


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
