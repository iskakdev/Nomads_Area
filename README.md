# Nomads Area — Backend API

> REST API для туристической платформы Nomads Area. Проект построен на Django, Django REST Framework, PostgreSQL, Celery и Redis.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.x-red)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.x-brightgreen?logo=celery)](https://docs.celeryq.dev)

---

## Содержание

1. [О проекте](#о-проекте)
2. [Стек](#стек)
3. [Production](#production)
4. [Быстрый старт локально](#быстрый-старт-локально)
5. [Celery и Redis](#celery-и-redis)
6. [API-эндпоинты](#api-эндпоинты)
7. [Фильтрация туров](#фильтрация-туров)
8. [Логика бронирования](#логика-бронирования)
9. [Отзывы](#отзывы)
10. [Актуальная структура backend](#актуальная-структура-backend)
11. [Переменные окружения](#переменные-окружения)
12. [Тесты и проверки](#тесты-и-проверки)
13. [Деплой backend](#деплой-backend)
14. [Деплой frontend](#деплой-frontend)
15. [Резервные копии](#резервные-копии)
16. [S3/CDN для медиа](#s3cdn-для-медиа)
17. [Sentry](#sentry)
18. [Smoke-проверки](#smoke-проверки)
19. [Нагрузочное тестирование](#нагрузочное-тестирование)
20. [Передача проекта разработчику](#передача-проекта-разработчику)

---

## О проекте

**Nomads Area** — платформа для просмотра и бронирования туров по Кыргызстану и Центральной Азии.

Пользовательская часть работает без клиентской авторизации: пользователь открывает каталог, выбирает тур, отправляет бронь, контактную заявку или проходит квиз. Менеджер обрабатывает заявки через Django Admin и получает уведомления в Telegram/Email.

### Основные возможности

- Каталог туров с фильтрацией по типу тура, стране, городу, категории, цене, сезону, сложности, датам и другим параметрам.
- Бронирование с серверным расчётом цены.
- Дедупликация повторных заявок через fingerprint.
- Атомарное резервирование мест при подтверждении брони.
- Контактные заявки и квиз для лидогенерации.
- Уведомления в Telegram и Email через Celery.
- Мультиязычность RU/EN/ES/FR/DE через URL-префикс.
- Отзывы через внешние виджеты Elfsight.
- Онлайн-платежи и трансферы удалены; оплата обрабатывается менеджером вручную.

---

## Стек

| Компонент | Технология |
|---|---|
| Backend | Python 3.12, Django 5.2 |
| API | Django REST Framework |
| База данных | PostgreSQL |
| Очереди | Celery + Redis |
| API-документация | drf-spectacular, Swagger, ReDoc |
| Переводы | django-modeltranslation |
| Уведомления | Telegram Bot API, SMTP |
| Production | Gunicorn + Nginx |
| Static files | Whitenoise |
| Admin UI | Django Admin / Jazzmin |

---

## Production

| Ресурс | Значение |
|---|---|
| Публичный сайт | `https://www.nomadsarea.com` |
| Backend API | `https://www.nomadsarea.com/api/...` |
| Swagger | `https://www.nomadsarea.com/api/docs/` |
| ReDoc | `https://www.nomadsarea.com/api/redoc/` |
| Admin | `https://www.nomadsarea.com/admin/` |
| VPS | Contabo VPS, Ubuntu |
| Backend path | `/root/Nomads_Area` |
| Django path | `/root/Nomads_Area/nomads_area` |
| Backend venv | `/root/Nomads_Area/venv` |
| Backend service | `nomadsarea` |
| Celery service | `nomadsarea-celery` |
| Frontend path | `/root/nomads-area` |
| Frontend process | `nomads-frontend` через PM2 |

---

## Быстрый старт локально

### 1. Клонировать проект

```bash
git clone https://github.com/iskakdev/Nomads_Area.git
cd Nomads_Area
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Установить зависимости

Можно из корня:

```bash
pip install -r requirements.txt
```

Или из Django-директории:

```bash
cd nomads_area
pip install -r requirements.txt
```

Основной файл зависимостей backend находится здесь:

```text
nomads_area/requirements.txt
```

Корневой `requirements.txt` оставлен для удобного деплоя и ссылается на основной файл.

### 4. Настроить окружение

```bash
cd nomads_area
cp .env.example .env
```

Минимальный `.env` для локального запуска:

```dotenv
DEBUG=True
SECRET_KEY=django-insecure-local-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=nomads_area
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

CACHE_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
```

### 5. Поднять PostgreSQL

На Arch Linux:

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql --no-pager
```

### 6. Применить миграции

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Запустить Django

```bash
python manage.py runserver
```

Локальные адреса:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/admin/
http://127.0.0.1:8000/api/docs/
```

---

## Celery и Redis

### Запуск Redis

```bash
redis-server
```

Или через systemd:

```bash
sudo systemctl start redis
```

### Запуск Celery worker

```bash
cd /home/iskhak/PycharmProjects/Nomads_Area/nomads_area
source ../.venv/bin/activate
celery -A nomads_area worker -l info
```

На Windows:

```bash
celery -A nomads_area worker -l info --pool=solo
```

> `tasks.py` намеренно оставлен отдельным файлом, потому что Celery autodiscover обычно ожидает задачи в модуле `nomads_area_app.tasks`.

---

## API-эндпоинты

Все публичные языковые эндпоинты имеют префикс:

```text
/api/ru/
/api/en/
/api/es/
/api/fr/
/api/de/
```

### Health

```text
GET /api/healthz/
GET /api/readyz/
```

### Контент

```text
GET /api/ru/site-settings/
GET /api/ru/team/
GET /api/ru/countries/
GET /api/ru/countries/{id}/
GET /api/ru/cities/
GET /api/ru/cities/{id}/
GET /api/ru/categories/
GET /api/ru/categories/{id}/
GET /api/ru/tours/
GET /api/ru/tours/{id}/
GET /api/ru/attractions/
GET /api/ru/attractions/{id}/
```

### Формы

```text
POST /api/ru/bookings/
POST /api/ru/contact/
POST /api/ru/quiz/submit/
GET  /api/ru/quiz/questions/
POST /api/ru/quiz/progress/
PUT  /api/ru/quiz/progress/save/{session_key}/
```

### Документация

```text
GET /api/docs/
GET /api/redoc/
GET /api/schema/
```

---

## Фильтрация туров

Примеры:

```text
GET /api/ru/tours/?tour_type=group&country=1&price_min=200&price_max=800
GET /api/ru/tours/?season=warm&difficulty=2&duration_min=3
GET /api/ru/tours/?exclude_sold_out=true&date_from=2026-06-01
GET /api/ru/tours/?search=озеро&ordering=-created_at
```

| Параметр | Значения | Описание |
|---|---|---|
| `tour_type` | `group`, `private` | Тип тура |
| `country` | ID | Страна |
| `city` | ID | Город |
| `category` | ID | Категория |
| `difficulty` | `1`, `2`, `3` | Лёгкий / средний / сложный |
| `season` | `all_year`, `warm`, `winter` | Сезон |
| `price_min`, `price_max` | число | Диапазон цен |
| `duration_min`, `duration_max` | число | Длительность в днях |
| `date_from` | `YYYY-MM-DD` | Дата заезда не раньше |
| `exclude_sold_out` | `true` | Скрыть распроданные |
| `search` | строка | Поиск по туру |
| `ordering` | `price`, `duration_days`, `created_at` | Сортировка |

---

## Логика бронирования

```text
Пользователь
  ↓
POST /api/{locale}/bookings/
  ↓
Валидация данных
  ↓
Расчёт цены на backend
  ↓
transaction.atomic()
  ↓
Создание Booking со статусом pending
  ↓
transaction.on_commit()
  ↓
Celery → Telegram + Email
  ↓
Менеджер подтверждает бронь в Django Admin
  ↓
transaction.atomic() + select_for_update()
  ↓
Статус confirmed + списание available_spots
```

Важные правила:

- Цена считается на backend, а не доверяется frontend.
- Для групповых туров проверяются свободные места.
- Для приватных туров пользователь может указать желаемые даты.
- Дополнительные услуги должны относиться к выбранному туру.
- Повторные заявки дедуплицируются через fingerprint.
- Места списываются только при подтверждении брони менеджером.

---

## Отзывы

Собственная база отзывов в проекте отсутствует.

Отзывы отображаются через внешние виджеты:

| Виджет | Источник | Настройка |
|---|---|---|
| Google Reviews | Elfsight | App ID в настройках сайта |
| TripAdvisor | Elfsight или внешний сервис | App ID / настройки виджета |

Настройки находятся в Django Admin:

```text
Настройки сайта → Виджеты отзывов
```

---

## Актуальная структура backend

После рефакторинга крупные backend-модули разделены по доменам.

```text
nomads_area_app/
├── admin/
│   ├── __init__.py
│   ├── common.py
│   ├── inlines.py
│   ├── content.py
│   ├── tours.py
│   ├── bookings.py
│   └── quiz.py
├── notifications/
│   ├── __init__.py
│   ├── common.py
│   ├── bookings.py
│   ├── contacts.py
│   └── quiz.py
├── serializers/
│   ├── __init__.py
│   ├── common.py
│   ├── content.py
│   ├── tours.py
│   ├── bookings.py
│   └── quiz.py
├── services/
│   ├── __init__.py
│   ├── common.py
│   ├── bookings.py
│   ├── contacts.py
│   └── quiz.py
├── tests/
│   ├── __init__.py
│   ├── base.py
│   ├── test_api_structure.py
│   ├── test_health.py
│   ├── test_integrity.py
│   └── test_project.py
├── views/
│   ├── __init__.py
│   ├── common.py
│   ├── health.py
│   ├── content.py
│   ├── tours.py
│   ├── bookings.py
│   └── quiz.py
├── models.py
├── urls.py
├── filters.py
├── tasks.py
├── translation.py
├── signals.py
├── middleware.py
├── throttles.py
├── exceptions.py
└── apps.py
```

### Назначение пакетов

#### `admin/`

Django Admin, разделённый по доменам:

- `common.py` — общие настройки админки и mixin для переводов.
- `inlines.py` — inline-классы Django Admin.
- `content.py` — настройки сайта, страны, города, категории, FAQ, доп. услуги.
- `tours.py` — туры, даты туров, достопримечательности.
- `bookings.py` — бронирования и контактные заявки.
- `quiz.py` — вопросы квиза и лиды.

#### `serializers/`

DRF serializers:

- `common.py` — общие helper-функции, локализация, URL файлов.
- `tours.py` — туры, страны, города, категории, достопримечательности.
- `bookings.py` — бронирования и контактные заявки.
- `quiz.py` — квиз.
- `content.py` — настройки сайта и команда.

#### `views/`

DRF views и viewsets:

- `common.py` — общий cache decorator.
- `health.py` — healthz и readyz.
- `content.py` — настройки сайта и команда.
- `tours.py` — туры, страны, города, категории, достопримечательности.
- `bookings.py` — создание броней и контактных заявок.
- `quiz.py` — квиз и лиды.

#### `services/`

Бизнес-логика:

- `common.py` — money helpers, fingerprint, dedup helpers.
- `bookings.py` — создание брони и расчёт цены.
- `quiz.py` — прогресс квиза и создание quiz lead.
- `contacts.py` — создание контактной заявки.

#### `notifications/`

Сборка и отправка уведомлений через Celery tasks:

- `common.py` — escaping и безопасная постановка задачи в очередь.
- `bookings.py` — уведомления о бронях.
- `quiz.py` — уведомления о лидах из квиза.
- `contacts.py` — уведомления о контактных заявках.

### Файлы, которые намеренно оставлены одиночными

| Файл | Почему не дробим |
|---|---|
| `models.py` | DB-схема, миграции и modeltranslation завязаны на модели. Разделять рискованно без отдельного плана. |
| `tasks.py` | Celery autodiscover ожидает задачи в `nomads_area_app.tasks`. |
| `urls.py` | Маршруты компактные и должны оставаться прозрачными. |
| `translation.py` | Регистрация modeltranslation. |
| `signals.py` | Django signals. |
| `filters.py` | Фильтры DRF. |
| `middleware.py` | Middleware. |

---

## Переменные окружения

Production `.env` находится здесь:

```text
/root/Nomads_Area/nomads_area/.env
```

Основные переменные:

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` или `False`; на production только `False` |
| `ALLOWED_HOSTS` | Разрешённые хосты через запятую |
| `DB_NAME` | Имя PostgreSQL базы |
| `DB_USER` | PostgreSQL пользователь |
| `DB_PASSWORD` | PostgreSQL пароль |
| `DB_HOST` | Обычно `localhost` |
| `DB_PORT` | Обычно `5432` |
| `CACHE_URL` | Redis cache URL |
| `CELERY_BROKER_URL` | Redis URL для Celery broker |
| `CELERY_RESULT_BACKEND` | Redis URL для Celery result backend |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений |
| `EMAIL_HOST_USER` | SMTP/Gmail пользователь |
| `EMAIL_HOST_PASSWORD` | Пароль приложения SMTP/Gmail |
| `DEFAULT_FROM_EMAIL` | Email отправителя |
| `API_DOCS_ENABLED` | Включить Swagger/ReDoc |
| `CORS_ALLOWED_ORIGINS` | Разрешённые frontend origins |
| `CSRF_TRUSTED_ORIGINS` | Доверенные origins для CSRF |

> Никогда не храните реальные секреты, токены и пароли в README, GitHub или чатах.

---

## Тесты и проверки

### Полный локальный тест

```bash
cd /home/iskhak/PycharmProjects/Nomads_Area
source .venv/bin/activate
cd nomads_area
python manage.py check
python manage.py test
```

Ожидаемо:

```text
Found 39 test(s).
OK
```

### Если PostgreSQL выключен локально

Ошибка будет похожа на:

```text
connection to server at "localhost", port 5432 failed: Connection refused
```

Решение на Arch Linux:

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql --no-pager
```

После этого повторить:

```bash
python manage.py check
python manage.py test
```

### Проверки без создания тестовой базы

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python -m compileall nomads_area nomads_area_app
bash -n ../scripts/*.sh
```

### Генерация OpenAPI схемы

```bash
python manage.py spectacular --file schema.yaml --validate
```

---

## Деплой backend

Production-команды:

```bash
ssh root@your-server-ip

cd /root/Nomads_Area
git pull --ff-only origin main

source venv/bin/activate
pip install -r requirements.txt

cd nomads_area
python manage.py migrate
python manage.py check

sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
sudo systemctl is-active nomadsarea nomadsarea-celery

cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

Проверка health:

```bash
curl -fsS https://www.nomadsarea.com/api/healthz/
curl -fsS https://www.nomadsarea.com/api/readyz/
```

Если сразу после `restart` появляется `502 Bad Gateway`, подождите 1–3 секунды: Gunicorn workers могут ещё подниматься.

---

## Деплой frontend

```bash
ssh root@your-server-ip

cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

---

## Резервные копии

### Backup базы данных

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

### Backup media

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

### Автоматические backup timers

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Расписание по умолчанию:

- база данных — каждый день в `03:15`;
- media — каждый день в `03:35`;
- срок хранения — 14 дней.

Проверка timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

### Проверка восстановления базы

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

Скрипт создаёт временную PostgreSQL-базу, восстанавливает dump, проверяет наличие таблиц и удаляет временную базу.

---

## S3/CDN для медиа

S3-совместимое хранилище опционально. Не включайте его без плана миграции уже загруженных файлов.

Пример `.env`:

```dotenv
USE_S3_STORAGE=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=...
AWS_S3_ENDPOINT_URL=...
AWS_S3_CUSTOM_DOMAIN=cdn.example.com
AWS_LOCATION=media
```

После изменения `.env`:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py check
sudo systemctl restart nomadsarea
```

Если задан `AWS_S3_CUSTOM_DOMAIN`, API будет отдавать media URL через CDN-домен.

---

## Sentry

Sentry опционален и не работает, пока не задан `SENTRY_DSN`.

Пример `.env`:

```dotenv
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

После изменения:

```bash
sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
```

`SENTRY_TRACES_SAMPLE_RATE=0.0` означает: ошибки отправляются, трассировка производительности выключена.

---

## Smoke-проверки

### Health

```bash
curl -fsS https://www.nomadsarea.com/api/healthz/
curl -fsS https://www.nomadsarea.com/api/readyz/
```

### Языковые версии тура

```bash
for locale in ru en es fr de; do
  curl -fsS "https://www.nomadsarea.com/api/$locale/tours/54/" >/dev/null \
    && echo "$locale OK" \
    || echo "$locale FAIL"
done
```

### Фильтр достопримечательностей

```bash
curl -fsS "https://www.nomadsarea.com/api/ru/attractions/?country=Казахстан" >/dev/null \
  && echo "Attractions filter OK"
```

### Удалённые payments

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://www.nomadsarea.com/api/en/payments/finikpay/webhook/
```

Ожидаемо:

```text
404
```

### Общий smoke script

```bash
cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

Ожидаемый результат:

```text
ru tour detail OK
en tour detail OK
es tour detail OK
fr tour detail OK
de tour detail OK
attractions country filter OK
smoke checks OK
```

---

## Нагрузочное тестирование

Не запускайте массовый POST на production. POST создаёт реальные брони, лиды и уведомления.

Для GET-нагрузки используйте отдельную VPS, не сервер приложения.

### Подготовка

Временно убедитесь, что включён общий Redis-кэш и высокий лимит для анонимных GET-запросов:

```dotenv
CACHE_URL=redis://127.0.0.1:6379/1
CACHE_KEY_PREFIX=nomads-area
API_CACHE_TIMEOUT=60
DRF_ANON_THROTTLE_RATE=1000000/minute
```

Не меняйте `DRF_FORMS_THROTTLE_RATE`: POST-формы не входят в этот тест.

### Запуск через k6

```bash
TARGET_URL=https://www.nomadsarea.com/api/en/tours/54/ \
ALLOW_PRODUCTION=yes \
VUS_LOW=10 \
VUS_HIGH=50 \
./loadtest/run.sh
```

Увеличивайте нагрузку отдельными запусками:

```text
10 → 25 → 50 → 100 VUS
```

Между запусками делайте паузу минимум 30 секунд.

Остановитесь, если:

- p99 выше 1.5–3 секунд;
- появились 5xx;
- появились worker timeout;
- CPU стабильно выше 90%;
- растёт swap;
- подключения PostgreSQL приближаются к лимиту.

### Мониторинг сервера

```bash
sudo journalctl -u nomadsarea -f
```

```bash
watch -n 1 'uptime; free -h; ss -s'
```

```bash
watch -n 2 "sudo -u postgres psql -Atc \"
SELECT state || ': ' || count(*)
FROM pg_stat_activity
GROUP BY state
ORDER BY state;
\""
```

После теста верните нормальный анонимный лимит и перезапустите Gunicorn.

---

## Передача проекта разработчику

Этот раздел нужен следующему разработчику, чтобы быстро понять проект и правила эксплуатации.

### Репозитории

Backend:

```text
GitHub: iskakdev/Nomads_Area
Production path: /root/Nomads_Area
Django path: /root/Nomads_Area/nomads_area
Venv: /root/Nomads_Area/venv
Service: nomadsarea
Celery service: nomadsarea-celery
```

Frontend:

```text
GitHub: kubanych-js/nomads-area
Production path: /root/nomads-area
Process manager: PM2
Process name: nomads-frontend
```

### Критичные правила

- Не хранить секреты в репозитории.
- Не включать `DEBUG=True` на production.
- Перед миграциями и крупными изменениями данных делать backup.
- Не запускать массовые POST-нагрузочные тесты на production.
- Не менять поведение кэша frontend без отдельного решения.
- Backend должен отклонять бронь на неактивный тур, даже если frontend показывает старую страницу.
- Достопримечательность должна быть одной записью и связываться с несколькими турами, а не дублироваться.
- Ветвление квиза должно оставаться в рамках выбранной ветки.

### Проверка `DEBUG=False`

```bash
cd /root/Nomads_Area/nomads_area
grep -n '^DEBUG=' .env
curl -sS -i https://www.nomadsarea.com/api/ru/not-existing-debug-check/ | head -40
```

Ожидаемо: обычный `404 Not Found`, без Django traceback-страницы.

### GitHub Actions

Если добавляется или изменяется workflow в `.github/workflows/`, нужен GitHub token с правом `workflow`. Не передавайте токены в чат. Лучше добавлять workflow через GitHub UI или короткоживущий token с минимальными правами.

---

## Дополнительная документация

- `MANAGER_GUIDE.md` — руководство менеджера по работе с админкой.
- `docs/Architecture.docx` — архитектура backend в Word-формате.
- `docs/backend_structure.md` — краткое описание структуры backend-приложения.
