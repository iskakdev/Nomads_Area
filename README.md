# Nomads Area - бэкенд API

> REST API для туристической платформы по Центральной Азии. Django + DRF + PostgreSQL.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green?logo=django)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.x-red)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.x-brightgreen?logo=celery)](https://docs.celeryq.dev)

---

## О проекте

Nomads Area - платформа для бронирования туров по Кыргызстану и Центральной Азии.

Система работает без клиентской авторизации: пользователь просматривает туры, бронирует тур или оставляет заявку. Менеджер обрабатывает всё через Django Admin и получает уведомления в Telegram.

**Что умеет система:**
- Каталог туров с фильтрацией по 10+ параметрам
- Бронирование с расчётом цены на сервере
- Атомарная дедупликация броней через hash + select_for_update (без race condition)
- Атомарное резервирование мест при подтверждении брони
- Контактные заявки и квиз с лидогенерацией
- Уведомления в Telegram и Email через Celery (transaction.on_commit)
- Мультиязычность RU/EN/ES/FR/DE через URL-префикс
- Отзывы через внешние виджеты Elfsight
- Онлайн-платежи и трансферы удалены; оплата обрабатывается физически/вручную

---

## Стек

| Компонент | Технология |
|-----------|------------|
| Бэкенд | Python 3.12, Django 5.2 |
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
| Админка | https://nomadsarea.com/admin/ |

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

## API-эндпоинты

Все публичные эндпоинты имеют языковой префикс: `/api/ru/`, `/api/en/`, `/api/es/`, `/api/fr/`, `/api/de/`.

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
       |
  [transaction.atomic]
  Booking(status=pending)
  [/transaction.atomic]
       |
  Менеджер подтверждает вручную через Admin
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

Собственная БД отзывов в проекте отсутствует. Отзывы отображаются через внешние виджеты:

- **Google Reviews** - Elfsight Google Reviews Widget (настраивается через App ID)
- **TripAdvisor** - Elfsight/внешний виджет, если он подключён на фронтенде

Настройки хранятся в Django Admin: Настройки сайта -> раздел "Виджеты отзывов".

---

## Структура проекта

```
Nomads_Area/
+-- nomads_area/
|   +-- settings.py
|   +-- urls.py
|   +-- celery.py
|   +-- wsgi.py
+-- nomads_area_app/
    +-- models.py
    +-- serializers.py
    +-- views.py
    +-- urls.py
    +-- filters.py
    +-- services.py
    +-- notifications.py
    +-- tasks.py
    +-- translation.py
    +-- admin.py
    +-- ограничение частоты запросовs.py
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
| `EMAIL_HOST_PASSWORD` | пароль приложения Gmail |
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

Дополнительные документы:

- `MANAGER_GUIDE.md` - руководство менеджера.
- `docs/Architecture.docx` - архитектура бэкенда в Word-формате.


---

# Чеклист эксплуатации
Документ для безопасной эксплуатации production. Не храните здесь пароли, токены, SMTP-ключи и доступы.

## 1. Деплой бэкенда

```bash
cd /root/Nomads_Area
git pull --ff-only origin main

source venv/bin/activate
cd nomads_area

python manage.py migrate
python manage.py check

sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
sudo systemctl is-active nomadsarea nomadsarea-celery
```

## 2. Деплой фронтенда

```bash
cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

## 3. Резервная копия базы данных

Создавайте backup перед миграциями и крупными изменениями данных.

Ручной backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

По умолчанию backup хранится в `/var/backups/nomads-area`, старые резервная копия БД старше 14 дней удаляются.

Проверка восстановления backup:

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

Скрипт создаёт временную PostgreSQL базу, восстанавливает dump, проверяет наличие таблиц и удаляет временную базу.

## 4. Резервная копия медиафайлов

Файлы из `MEDIA_ROOT` нужно бэкапить отдельно от PostgreSQL.

Ручной backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

По умолчанию media backup хранится в `/var/backups/nomads-area`, старые media backup старше 14 дней удаляются.

## 5. Автоматические резервные копии

Установить systemd timers:

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Расписание:

- резервная копия БД: каждый день в 03:15
- резервная копия медиа: каждый день в 03:35

Проверить timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

## 6. Хранение медиафайлов и CDN

Сейчас media может храниться на сервере. Для роста проекта лучше вынести media в S3-совместимое хранилище и CDN, чтобы сервер не был единственной точкой хранения фотографий и видео.

Бэкенд уже поддерживает режим включения через переменные окружения. В `.env`:

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

Если `AWS_S3_CUSTOM_DOMAIN` задан, API будет отдавать media URL через CDN-домен.

После изменения env:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py check
sudo systemctl restart nomadsarea
```

## 7. Мониторинг ошибок

Для Sentry достаточно добавить DSN в `.env`:

```dotenv
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

После изменения env:

```bash
sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
```

`SENTRY_TRACES_SAMPLE_RATE=0.0` означает: ошибки отправляются, трассировка производительности выключена. Если потом понадобится мониторинг производительности, можно поднять до `0.05` или `0.1`.

## 8. Smoke-проверки после деплоя

```bash
for locale in ru en es fr de; do
  curl -fsS "https://www.nomadsarea.com/api/$locale/tours/54/" >/dev/null \
    && echo "$locale OK" \
    || echo "$locale FAIL"
done
```

```bash
curl -fsS "https://www.nomadsarea.com/api/ru/attractions/?country=Казахстан" >/dev/null \
  && echo "Attractions filter OK"
```

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  https://www.nomadsarea.com/api/en/payments/finikpay/webhook/
```

Ожидаемо: `404`, потому что онлайн-платежи удалены.

Или одной командой:

```bash
cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

## 9. Правила нагрузочного тестирования

Не запускать массовый POST на production. Он создаёт реальные брони/лиды/уведомления.

Для честного GET-теста:

- запускать нагрузку с отдельной VPS;
- заранее проверить, что ограничение частоты запросов не превращает тест в поток `429`;
- мониторить `journalctl`, RAM, CPU, подключения PostgreSQL;
- прекращать тест при `5xx`, таймаут worker-процесса, росте swap или p99 выше 2-3 секунд.

Пример wrk:

```bash
/usr/bin/wrk -t2 -c10 -d30s --latency \
  https://www.nomadsarea.com/api/en/tours/54/
```

## 10. Безопасность данных из админки

- Если тур выключен через `Активен`, backend не должен принимать новую бронь на этот тур.
- Достопримечательность должна быть одной записью, связанной с несколькими турами, а не дублями.
- Если меняются вопросы квиза, проверяйте ветвление: выбранная ветка не должна показывать вопросы из другой ветки.


---

# Передача проекта разработчику

Этот документ нужен следующему разработчику, чтобы быстро понять текущее состояние проекта, правила работы и критичные места. Не храните здесь секреты, токены, пароли и реальные ключи.

## Репозитории и production-пути

Бэкенд:

- GitHub: `iskakdev/Nomads_Area`
- Путь на production: `/root/Nomads_Area`
- Путь Django-проекта: `/root/Nomads_Area/nomads_area`
- Виртуальное окружение: `/root/Nomads_Area/venv`
- Основной сервис: `nomadsarea`
- Celery-сервис: `nomadsarea-celery`

Фронтенд:

- GitHub: `kubanych-js/nomads-area`
- Путь на production: `/root/nomads-area`
- Менеджер процессов: PM2
- PM2-процесс: `nomads-frontend`

Production-домен:

- Публичный сайт: `https://www.nomadsarea.com`
- API бэкенда доступен через `/api/...` и проксируется Nginx.

## Текущий стек бэкенда

- Django 5.2.x
- Django REST Framework
- PostgreSQL
- Redis-кэш
- Celery
- django-modeltranslation для полей моделей RU/EN/ES/FR/DE
- админка на django-jazzmin
- Sentry опционален и выключен, пока не задан `SENTRY_DSN`
- S3-совместимое хранилище медиа опционально и выключено, пока не задано `USE_S3_STORAGE=True`

## Файлы зависимостей

Единственный основной список зависимостей бэкенда:

- `nomads_area/requirements.txt`

Файл в корне репозитория оставлен только для удобного деплоя:

- `requirements.txt` содержит `-r nomads_area/requirements.txt`

Поэтому работают обе команды:

```bash
cd /root/Nomads_Area
pip install -r requirements.txt
```

```bash
cd /root/Nomads_Area/nomads_area
pip install -r requirements.txt
```

При добавлении зависимостей бэкенда обновляйте только `nomads_area/requirements.txt`.

## Обязательное production-окружение

Production-файл окружения на сервере:

```bash
/root/Nomads_Area/nomads_area/.env
```

Важные переменные:

```dotenv
DEBUG=False
SECRET_KEY=...
ALLOWED_HOSTS=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
CACHE_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=https://www.nomadsarea.com,https://nomadsarea.com
```

`DEBUG` должен оставаться `False` на production. Если поставить `True`, Django может показать debug-страницы с внутренними настройками и stack trace.

## Health- и smoke-проверки

Публичные health-эндпоинты:

```bash
curl -fsS https://www.nomadsarea.com/api/healthz/
curl -fsS https://www.nomadsarea.com/api/readyz/
```

Полная smoke-проверка:

```bash
cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

Ожидаемый вывод содержит:

```text
ru tour detail OK
en tour detail OK
es tour detail OK
fr tour detail OK
de tour detail OK
attractions country filter OK
smoke checks OK
```

## Деплой бэкенда

```bash
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

## Деплой фронтенда

```bash
cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

## Резервные копии и восстановление

Ручная резервная копия базы данных:

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

Ручная резервная копия медиафайлов:

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

Установка автоматических systemd timers:

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Расписание по умолчанию:

- резервная копия базы данных каждый день в 03:15
- резервная копия медиафайлов каждый день в 03:35
- срок хранения резервных копий: 14 дней

Проверка timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

Проверка восстановления базы данных:

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

Проверка восстановления создаёт временную PostgreSQL-базу, восстанавливает dump, проверяет наличие таблиц в схеме public и удаляет временную базу.

## Опциональная настройка Sentry

Sentry опционален и не работает, пока не задан `SENTRY_DSN`.

Добавить в `.env`:

```dotenv
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

Затем:

```bash
sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
```

Сначала используйте `SENTRY_TRACES_SAMPLE_RATE=0.0`: ошибки будут отправляться, а трассировка производительности будет выключен. Поднимайте до `0.05` или `0.1` только если нужны данные производительности.

## Опциональная настройка S3/CDN для медиа

S3-совместимое хранилище опционально и по умолчанию выключено.

Добавляйте в `.env` только после подготовки bucket/CDN:

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

Затем:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py check
sudo systemctl restart nomadsarea
```

Не включайте S3 без плана миграции медиафайлов. Уже загруженные локальные файлы сами не переедут в S3.

## Важная бизнес-логика

### Активные туры

Если тур неактивен, фронтенд должен перестать показывать его после обновления кэша/ревалидации, но бэкенд также обязан отклонять попытки бронирования. Проверка на бэкенде - финальный защитный слой.

### Бронирования

При создании брони проверяется:

- тур существует;
- тур активен;
- выбранная дата относится к выбранному туру;
- дополнительные услуги относятся к выбранному туру;
- для группового тура есть свободные места;
- дубли заявок обрабатываются через fingerprint.

### Достопримечательности

Достопримечательность должна быть одной записью, связанной со многими турами, а не дублем под каждый тур.

Правильная схема:

```text
Достопримечательность
  ├── приватный тур A
  ├── групповой тур B
  └── приватный тур C
```

Фильтрация достопримечательностей по стране:

```text
/api/ru/attractions/?country=Казахстан
/api/ru/attractions/?country=Kazakhstan
/api/ru/attractions/?country=<country_id>
```

### Ветвление квиза

Ветвление квиза должно останавливаться на выбранной ветке. Вариант ответа с `next_question` ведёт только в свою ветку. Другие ветки не должны появляться после выбора конкретной ветки.

## Правило по кэшу

Политика кэша/ревалидации фронтенда намеренно оставлена как есть после последнего обсуждения. Не меняйте поведение кэша фронтенда без отдельного решения.

Бэкенд всё равно защищает критичные действия. Например: даже если старая страница фронтенда показывает неактивный тур, бэкенд должен отклонить бронирование.

## Известные эксплуатационные нюансы

- `https://www.nomadsarea.com/healthz/` может попасть во фронтенд или редирект в зависимости от Nginx. Для проверки бэкенда используйте `/api/healthz/` и `/api/readyz/`.
- `/api/not-existing-debug-check/` может быть интерпретирован как маршрут с языком. Для проверки реального 404 используйте `/api/ru/not-existing-debug-check/`.
- `DEBUG=False` нужно проверять после деплоя:

```bash
cd /root/Nomads_Area/nomads_area
grep -n '^DEBUG=' .env
curl -sS -i https://www.nomadsarea.com/api/ru/not-existing-debug-check/ | head -40
```

Ожидаемо: `404 Not Found`, без Django traceback-страницы.

- Не запускайте разрушительные DB-команды на production без свежей резервной копии.
- Не запускайте массовые POST-нагрузочные тесты на production. Они создают реальные лиды, брони и уведомления.

## Тесты

Локальные/полные тесты бэкенда:

```bash
cd /home/iskhak/PycharmProjects/Nomads_Area
source .venv/bin/activate
python nomads_area/manage.py test nomads_area_app
```

Последнее ожидаемое количество - 39 тестов. Если тестовая PostgreSQL-база уже существует, Django спросит, удалить ли её; отвечайте `yes` только для локальной/тестовой базы.

Проверки без тестовой базы данных:

```bash
python nomads_area/manage.py check
python nomads_area/manage.py makemigrations --check --dry-run
python -m compileall nomads_area/nomads_area nomads_area/nomads_area_app
bash -n scripts/*.sh
```

## GitHub Actions

CI workflow намеренно не закоммичен, потому что push workflow-файлов требует GitHub token с правом `workflow`. Владелец проекта сказал, что сделает эту часть сам.

Не просите токены в чате. Если добавляете CI, используйте короткоживущий token с ограниченными правами на репозиторий и правом `workflow`, либо добавьте workflow через GitHub UI.


---

# Нагрузочное тестирование

Запускайте генератор нагрузки с отдельной VPS, не с сервера приложения. Тест использует только эндпоинт детальной страницы тура только для чтения и считает редиректы, ограничение частоты запросов и серверные ошибки провалом.

## Подготовка production

Настройте Django на общий Redis-кэш и временно поднимите только анонимный лимит чтения:

```env
CACHE_URL=redis://127.0.0.1:6379/1
CACHE_KEY_PREFIX=nomads-area
API_CACHE_TIMEOUT=60
DRF_ANON_THROTTLE_RATE=1000000/minute
```

Перезапустите Gunicorn и проверьте, что повторные запросы возвращают `200`. Не меняйте `DRF_FORMS_THROTTLE_RATE`; POST-формы не входят в этот тест.

## Запуск

Установите k6 на VPS для генерации нагрузки, скопируйте туда директорию `loadtest`, затем запустите:

```bash
TARGET_URL=https://www.nomadsarea.com/api/en/tours/54/ \
ALLOW_PRODUCTION=yes \
VUS_LOW=10 \
VUS_HIGH=50 \
./loadtest/run.sh
```

Увеличивайте `VUS_HIGH` отдельными запусками: `10`, `25`, `50`, `100`, с паузой минимум 30 секунд между запусками. Остановитесь, если p99 выше 1.5 секунды, появились 5xx, таймаут worker-процесса, CPU держится выше 90%, растёт swap или подключения PostgreSQL приближаются к лимиту.

JSON-отчёт сохраняется в `loadtest/results/`.

## Мониторинг сервера

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

После production-теста верните нормальный анонимный лимит и перезапустите Gunicorn. Общий Redis-кэш оставьте включённым.
