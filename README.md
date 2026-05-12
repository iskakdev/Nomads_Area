# Nomads Area - Tourism Backend API

Backend на Django REST Framework для туристического сайта по Центральной Азии (Кыргызстан, Казахстан, Узбекистан).

## Стек

- Python 3.12+
- Django 5.2 + Django REST Framework
- PostgreSQL
- Celery + Redis (асинхронные уведомления)
- Telegram Bot API + Gmail SMTP
- drf-spectacular (Swagger документация)

## Архитектура

- **Публичный** - клиенты не регистрируются, оставляют заявки.
- **Менеджер** работает через Django Admin (`/admin/`).
- **Уведомления** в Telegram + Email при каждой заявке.
- **Атомарное списание мест** через `select_for_update()`.
- **Дедупликация** заявок (5-минутное окно).

## Установка

```bash
# 1. Клонировать репозиторий
git clone <repo-url>
cd nomads_area

# 2. Виртуальное окружение
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows

# 3. Зависимости
pip install -r requirements.txt

# 4. .env
cp .env.example .env
# Заполнить .env реальными значениями

# 5. База данных
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 6. Статика
python manage.py collectstatic --noinput
Запуск (3 терминала)
Bash

# Терминал 1 - Redis
redis-server

# Терминал 2 - Celery Worker
celery -A nomads_area worker -l info --pool=solo

# Терминал 3 - Django
python manage.py runserver
Адреса
Admin: http://127.0.0.1:8000/admin/
Swagger UI: http://127.0.0.1:8000/api/docs/
ReDoc: http://127.0.0.1:8000/api/redoc/
OpenAPI Schema: http://127.0.0.1:8000/api/schema/
API Endpoints
Публичные GET
text

/api/site-settings/
/api/team/
/api/countries/
/api/cities/
/api/categories/
/api/tours/
/api/tours/{id}/
/api/tour-dates/upcoming/
/api/attractions/
/api/transfer-routes/
/api/quiz/questions/
/api/quiz/progress/
Публичные POST (формы)
text

/api/bookings/             - заявка на тур
/api/quiz/submit/          - заявка с квиза
/api/transport-requests/   - заявка на трансфер
/api/contact/              - контактная форма
Фильтры туров
text

/api/tours/?country=1
/api/tours/?tour_type=group
/api/tours/?price_min=300&price_max=1000
/api/tours/?difficulty=2
/api/tours/?season=warm
/api/tours/?date_from=2026-06-01
/api/tours/?exclude_sold_out=true
Тесты
Bash

python manage.py test nomads_area_app
Документация
Полная документация API доступна в Swagger:
http://127.0.0.1:8000/api/docs/

OpenAPI schema для фронтенда:

Bash

python manage.py spectacular --file schema.yaml
Защита
Throttling: 5 заявок/минуту на одного клиента.
Атомарные транзакции при бронировании.
Server-side pricing (цены считает только сервер).
CORS настраивается через .env.
Структура проекта
text

nomads_area/
├── nomads_area/             # Конфигурация Django
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── nomads_area_app/         # Главное приложение
│   ├── models.py            # Модели БД
│   ├── serializers.py       # DRF сериализаторы
│   ├── views.py             # API endpoints
│   ├── urls.py              # URL роуты
│   ├── admin.py             # Django Admin
│   ├── filters.py           # Фильтры туров
│   ├── tasks.py             # Celery задачи
│   ├── notifications.py     # Уведомления
│   └── throttles.py         # Rate limiting
├── .env                     # Секреты (НЕ коммитить!)
├── .env.example             # Пример .env
├── requirements.txt
└── manage.py