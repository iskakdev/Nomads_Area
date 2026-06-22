from ..tasks import send_email_task, send_telegram_task
from .common import clean, enqueue_task_safely


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
