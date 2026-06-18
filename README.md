# Nomads Area - Backend API

> REST API для туристической платформы по Центральной Азии. Django + DRF + PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.x-red)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.x-brightgreen?logo=celery)](https://docs.celeryq.dev)

---

## О проекте

Nomads Area - платформа для бронирования туров по Кыргызстану и Центральной Азии.

Система работает без клиентской авторизации: пользователь просматривает туры, бронирует, заказывает трансфер или оставляет заявку. Менеджер обрабатывает всё через Django Admin и получает уведомления в Telegram.

**Что умеет система:**
- Каталог туров с фильтрацией по 10+ параметрам
- Бронирование с расчётом цены на сервере (30% предоплата)
- Атомарная дедупликация броней через hash + select_for_update (без race condition)
- Атомарное резервирование мест при подтверждении оплаты
- Трансферы, контактные заявки, квиз с лидогенерацией
- Уведомления в Telegram и Email через Celery (transaction.on_commit)
- Мультиязычность RU/EN через URL-префикс
- Отзывы через внешние виджеты (Google Reviews - Elfsight, TripAdvisor - официальный виджет)
- Платёжный провайдер - архитектура готова, подключение планируется

---

## Стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.12, Django 5.2 |
| API | Django REST Framework |
| База данных | PostgreSQL 16 |
| Очереди | Celery + Redis |
| Авто-документация | drf-spectacular (Swagger / ReDoc) |
| Переводы | django-modeltranslation |
| Уведомления | Telegram Bot API, SMTP |
| Деплой | Gunicorn + Nginx, Whitenoise |

---

## Продакшен

| | |
|---|---|
| Домен | https://nomadsarea.com |
| Сервер | Contabo VPS, Ubuntu 24.04 |
| Swagger | https://nomadsarea.com/api/docs/ |
| Admin | https://nomadsarea.com/admin/ |

---

## Быстрый старт

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/iskakdev/Nomads_Area.git
cd Nomads_Area/nomads_area
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настроить окружение

```bash
cp .env.example .env
```

Минимум для запуска:

```env
DEBUG=True
SECRET_KEY=django-insecure-your-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=nomads_area
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 3. Применить миграции и создать суперпользователя

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Запустить

```bash
python manage.py runserver
```

Сервер: `http://127.0.0.1:8000`

Swagger UI: `http://127.0.0.1:8000/api/docs/`

Django Admin: `http://127.0.0.1:8000/admin/`

---

## Celery (асинхронные уведомления)

```bash
# Запустить Redis
redis-server

# Запустить worker
celery -A nomads_area worker -l info

# Windows
celery -A nomads_area worker -l info --pool=solo
```

---

## Деплой на сервер

```bash
# Зайти на сервер
ssh root@your-server-ip

# Подтянуть изменения
cd /root/Nomads_Area/nomads_area
git pull

# Перезапустить сервис
systemctl restart nomadsarea
systemctl restart nomadsarea-celery
```

---

## API endpoints

Все endpoints имеют языковой префикс `/api/ru/` или `/api/en/`.

### Контент

```
GET  /api/ru/site-settings/
GET  /api/ru/team/
GET  /api/ru/countries/
GET  /api/ru/countries/{id}/
GET  /api/ru/cities/
GET  /api/ru/cities/{id}/
GET  /api/ru/categories/
GET  /api/ru/categories/{id}/
GET  /api/ru/tours/
GET  /api/ru/tours/{id}/
GET  /api/ru/attractions/
GET  /api/ru/attractions/{id}/
```

### Формы

```
POST /api/ru/bookings/
POST /api/ru/contact/
POST /api/ru/quiz/submit/
GET  /api/ru/quiz/questions/
POST /api/ru/quiz/progress/
PUT  /api/ru/quiz/progress/save/{session_key}/
```

### Оплата

```
POST /api/ru/payments/finikpay/webhook/
```

### Документация

```
GET  /api/docs/
GET  /api/redoc/
GET  /api/schema/
```

---

## Фильтрация туров

```
GET /api/ru/tours/?tour_type=group&country=1&price_min=200&price_max=800
GET /api/ru/tours/?season=warm&difficulty=2&duration_min=3
GET /api/ru/tours/?exclude_sold_out=true&date_from=2026-06-01
GET /api/ru/tours/?search=озеро&ordering=-created_at
```

| Параметр | Значения | Описание |
|----------|----------|----------|
| `tour_type` | `group`, `private` | Тип тура |
| `country` | ID | Страна |
| `city` | ID | Город |
| `category` | ID | Категория |
| `difficulty` | `1`, `2`, `3` | Легкий / Средний / Сложный |
| `season` | `all_year`, `warm`, `winter` | Сезон |
| `price_min` / `price_max` | число | Диапазон цен |
| `duration_min` / `duration_max` | число | Длительность (дней) |
| `date_from` | `YYYY-MM-DD` | Дата заезда не раньше |
| `exclude_sold_out` | `true` | Скрыть распроданные |
| `search` | строка | Полнотекстовый поиск |
| `ordering` | `price`, `duration_days`, `created_at` | Сортировка |

---

## Логика бронирования

```
Пользователь -> POST /bookings/
       |
  Валидация (даты, места, тип тура)
       |
  Расчёт цены на сервере
  price_per_person x people = total_price
  total_price x 30% = prepayment_amount
       |
  [transaction.atomic]
  Booking(status=pending) + Payment(status=pending)
  [/transaction.atomic]
       |
  Менеджер подтверждает вручную через Admin
  или webhook от платёжного провайдера
       |
  [transaction.atomic + select_for_update]
  Booking(status=confirmed)
  + списание мест TourDate.available_spots
  [/transaction.atomic]
       |
  transaction.on_commit -> Celery -> Telegram + Email
```

---

## Логика отзывов

Собственная БД отзывов в проекте отсутствует. Отзывы отображаются через два внешних виджета:

- **Google Reviews** - Elfsight Google Reviews Widget (платный, настраивается через App ID)
- **TripAdvisor** - официальный бесплатный виджет TripAdvisor (настраивается через embed-код)

Оба настраиваются в Django Admin: Настройки сайта -> раздел "Виджеты отзывов".

---

## Структура проекта

```
Nomads_Area/
+-- nomads_area/
|   +-- settings.py
|   +-- urls.py
|   +-- celery.py
|   +-- middleware.py
|   +-- wsgi.py
+-- nomads_area_app/
    +-- models.py
    +-- serializers.py
    +-- views.py
    +-- urls.py
    +-- filters.py
    +-- services.py
    +-- payment_providers.py
    +-- notifications.py
    +-- tasks.py
    +-- translation.py
    +-- admin.py
    +-- throttles.py
    +-- exceptions.py
```

---

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Через запятую |
| `DB_*` | Параметры PostgreSQL |
| `CELERY_BROKER_URL` | Redis URL |
| `TELEGRAM_BOT_TOKEN` | Токен бота |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений |
| `EMAIL_HOST_USER` | Gmail аккаунт |
| `EMAIL_HOST_PASSWORD` | App password Gmail |
| `FINIKPAY_API_KEY` | API ключ (зарезервировано) |
| `FINIKPAY_WEBHOOK_SECRET` | Секрет webhook (зарезервировано) |
| `FINIKPAY_RETURN_URL` | URL после оплаты (зарезервировано) |
| `API_DOCS_ENABLED` | Включить Swagger (`True`/`False`) |
| `CORS_ALLOWED_ORIGINS` | Разрешённые origins фронтенда |
| `CSRF_TRUSTED_ORIGINS` | Доверенные origins для CSRF |

---

## Тесты

```bash
python manage.py test nomads_area_app
```

Генерация OpenAPI схемы:

```bash
python manage.py spectacular --file schema.yaml --validate
```

---

## Документация

- [Руководство для менеджера](MANAGER_GUIDE.md)
- [Архитектура бэкенда](docs/Architecture.docx)
