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
        k = str(key).strip().lower()

        # Format
        if (
            "формат" in k
            or "type of travel" in k
            or "travel do you prefer" in k
            or "tipo de viaje" in k
            or "type de voyage" in k
            or "reiseart" in k
            or "art von reise" in k
        ):
            return "Format"

        # Region
        if (
            "регион" in k
            or "страна" in k
            or "куда" in k
            or "region" in k
            or "central asia" in k
            or "región" in k
            or "région" in k
            or "region zentralasiens" in k
        ):
            return "Region"

        # Budget
        if (
            "бюджет" in k
            or "budget" in k
            or "presupuesto" in k
            or "budget par personne" in k
        ):
            return "Budget"

        # Duration
        if (
            "сколько дней" in k
            or "дней" in k
            or "how many days" in k
            or "days do you have" in k
            or "cuántos días" in k
            or "combien de jours" in k
            or "wie viele tage" in k
        ):
            return "Duration"

        # Activity / interest
        if (
            "актив" in k
            or "интерес" in k
            or "activity" in k
            or "actividad" in k
            or "activité" in k
            or "aktivität" in k
        ):
            return "Activity"

        # Travel date
        if (
            "когда" in k
            or "планируете" in k
            or "when are you planning" in k
            or "planning to travel" in k
            or "cuándo" in k
            or "quand" in k
            or "wann" in k
        ):
            return "Travel date"

        # People
        if (
            "человек" in k
            or "people" in k
            or "how many people" in k
            or "personas" in k
            or "personnes" in k
            or "personen" in k
        ):
            return "People"

        # Requests
        if (
            "пожелания" in k
            or "special requests" in k
            or "solicitudes especiales" in k
            or "demandes spéciales" in k
            or "besondere wünsche" in k
        ):
            return "Requests"

        # Comfort
        if (
            "комфорт" in k
            or "прожив" in k
            or "accommodation comfort" in k
            or "comfort" in k
            or "alojamiento" in k
            or "hébergement" in k
            or "unterkunft" in k
        ):
            return "Comfort"

        # Contact
        if (
            "рекомендации" in k
            or "получить" in k
            or "receive recommendations" in k
            or "recommendations" in k
            or "recibir recomendaciones" in k
            or "recevoir" in k
            or "empfehlungen" in k
        ):
            return "Contact"

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
