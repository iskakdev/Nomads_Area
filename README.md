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

Все публичные endpoints имеют языковой префикс: `/api/ru/`, `/api/en/`, `/api/es/`, `/api/fr/`, `/api/de/`.

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

---

## Документация

Вся Markdown-документация проекта объединена в этом `README.md`, чтобы следующий разработчик и менеджер работали из одного файла.

Дополнительный не-Markdown документ:

- `docs/Architecture.docx` — архитектура backend в Word-формате.


---

# Руководство менеджера

> Это руководство поможет вам работать с административной панелью сайта Nomads Area.
> Здесь описано как добавлять туры, обрабатывать бронирования, отвечать на заявки и настраивать сайт.

**Адрес админ-панели:** https://nomadsarea.com/admin/

---

## Содержание

1. [Вход в систему](#1-вход-в-систему)
2. [Главная страница](#2-главная-страница)
3. [Настройки сайта](#3-настройки-сайта)
4. [Туры](#4-туры)
5. [Страны и города](#5-страны-и-города)
6. [Категории туров](#6-категории-туров)
7. [Бронирования](#7-бронирования)
8. [Контактные заявки](#8-контактные-заявки)
9. [Квиз и лиды](#9-квиз-и-лиды)
10. [Отзывы](#10-отзывы)
11. [Достопримечательности](#11-достопримечательности)
12. [Команда](#12-команда)
13. [Переводы RU/EN/ES/FR/DE](#13-переводы-ruenesfrde)
14. [FAQ по турам](#14-faq-по-турам)
15. [Частые вопросы](#15-частые-вопросы)

---

## 1. Вход в систему

Откройте браузер и перейдите по адресу:

```
https://nomadsarea.com/admin/
```

Введите логин и пароль. Если забыли пароль — обратитесь к разработчику.

---

## 2. Главная страница

После входа вы увидите список разделов. Вот что вам нужно чаще всего:

| Раздел | Для чего |
|--------|----------|
| **Туры** | Добавлять и редактировать туры |
| **Бронирования** | Обрабатывать заявки клиентов |
| **Контактные заявки** | Отвечать на обращения |
| **Лиды из квиза** | Обрабатывать заявки с квиза |
| **Настройки сайта** | Контакты, соцсети, тексты |

---

## 3. Настройки сайта

Раздел: **Настройки сайта → Настройки сайта**

Здесь хранится вся общая информация о компании, которая отображается на сайте.

> **Важно:** Настройки существуют в одном экземпляре. Не создавайте новую запись — редактируйте существующую.

### Контакты

| Поле | Описание |
|------|----------|
| Телефон | Основной номер |
| WhatsApp | Номер для WhatsApp |
| Email | Почта компании |

### Социальные сети

Ссылки на Instagram, Facebook, YouTube, TikTok, TripAdvisor.

### О компании

| Поле | Описание |
|------|----------|
| Текст "О нас" | Описание компании |
| Видео о компании | Загрузите видеофайл через поле выбора файла |
| Лет опыта | Цифра на главной странице |
| Количество туристов | Цифра статистики |
| Количество маршрутов | Цифра статистики |

---

## 4. Туры

Раздел: **Туры → Туры**

### Создание нового тура

Нажмите **+ Добавить тур** в правом верхнем углу.

---

### Основная информация

| Поле | Описание |
|------|----------|
| Название тура | Отображается на сайте |
| Тип тура | Групповой или Приватный |
| Активен | Включите, чтобы тур показывался на сайте |
| Страна | Выбрать из списка |
| Город | Основной город тура |
| Категории | Можно выбрать несколько |

---

### Параметры

| Поле | Описание |
|------|----------|
| Сезон | Круглый год / Тёплый / Зима |
| Длительность (дней) | Количество дней тура |
| Сложность | 1 — Лёгкий, 2 — Средний, 3 — Сложный |
| Максимум людей | Для групповых туров |
| Цена | За человека (для групповых) или минимальная (для приватных) |
| Валюта | USD или KGS |

---

### Описание

| Поле | Описание |
|------|----------|
| Описание | Краткое описание тура |
| Что включено | Список через запятую или текстом |
| Что не включено | Список через запятую или текстом |

---

### Фотографии

В блоке **Фото тура**:
- Нажмите **Добавить ещё одно фото**
- Загрузите фото (JPG или PNG, рекомендуется 1920×1080)
- Первое фото станет обложкой в каталоге

---

### Программа по дням

В блоке **Маршрут по дням** добавьте описание каждого дня тура:

| Поле | Описание |
|------|----------|
| Номер дня | 1, 2, 3... |
| Заголовок | Краткое название дня |
| Описание | Подробное описание |
| Высота | Например: 3500 м |
| Пешая дистанция | Например: 8 км |
| Дистанция на машине | Например: 120 км |
| Проживание | Юрта / Гостиница / Кемпинг |

---

### Даты заездов (только для групповых туров)

В блоке **Даты заезда**:

| Поле | Описание |
|------|----------|
| Дата начала | Дата старта тура |
| Дата окончания | Дата завершения |
| Доступные места | Количество свободных мест |

> Для **приватных туров** даты не нужны — клиент сам указывает желаемые даты при бронировании.

---

### Ценовые тиры (только для приватных туров)

В блоке **Цены приватных туров** укажите цену в зависимости от размера группы:

| Поле | Описание |
|------|----------|
| Минимум людей | Например: 1 |
| Максимум людей | Например: 3 (оставьте пустым — значит "и более") |
| Цена за человека | Например: 450 |

Пример заполнения:

```
1–2 чел  →  600$ за человека
3–5 чел  →  450$ за человека
6+  чел  →  350$ за человека
```

> Диапазоны не должны пересекаться — система покажет ошибку.

---

### Точки маршрута (карта)

В блоке **Точки маршрута** добавьте координаты для отображения на карте:
1. Найдите точку на Google Maps
2. Скопируйте широту и долготу
3. Укажите название точки

---

### Сохранение

Нажмите **Сохранить** в правом нижнем углу. Тур появится на сайте, если стоит галочка **Активен**.

---

## 5. Страны и города

### Страны

Раздел: **Туры → Страны**

| Поле | Описание |
|------|----------|
| Название страны | Отображается на сайте |
| Изображение | Главное фото |
| Символ страны | Иконка или флаг |
| Описание | Текст для страницы страны |

### Города

Раздел: **Туры → Города**

| Поле | Описание |
|------|----------|
| Страна | К какой стране относится |
| Название города | Отображается на сайте |
| Изображение города | Главное фото |

---

## 6. Категории туров

Раздел: **Туры → Категории туров**

Примеры: Горные туры, Конные туры, Культурные, Трекинг.

| Поле | Описание |
|------|----------|
| Название | Отображается на сайте |
| Иконка | Изображение категории |
| Активна | Показывать ли на сайте |

---

## 7. Бронирования

Раздел: **Бронирования → Бронирования**

Здесь отображаются все заявки на туры.

### Статусы

| Статус | Значение |
|--------|----------|
| **Ожидает** | Новая заявка, ожидает решения менеджера |
| **Подтверждён** | Бронь подтверждена, место зарезервировано |
| **Отменён** | Клиент или менеджер отменил |
| **Отклонён** | Нет мест или ошибка |

### Как подтвердить бронирование

1. Поставьте галочку рядом с бронированием
2. Выберите действие **Подтвердить и зарезервировать места**
3. Статус изменится на **Подтверждён**, места спишутся автоматически

---

### Массовые действия

1. Поставьте галочки на нужных бронях
2. В меню **Действие** выберите:
   - **Подтвердить и зарезервировать места**
   - **Отменить выбранные брони**

---

### Поля бронирования

| Поле | Описание |
|------|----------|
| Клиент | Имя и контакт |
| Тур | Название тура |
| Дата тура | Для групповых туров |
| Желаемые даты | Для приватных туров |
| Количество людей | Взрослые + дети |
| Цена за человека | Рассчитана системой |
| Итоговая цена | Полная стоимость |
| Статус | Текущий статус |

---

## 8. Контактные заявки

Раздел: **Контакты → Контактные заявки**

Обращения с контактной формы сайта.

### Как обработать

1. Откройте заявку
2. Свяжитесь с клиентом по указанному контакту
3. Измените статус на **Отвечено**

### Статусы

| Статус | Значение |
|--------|----------|
| **Ожидает ответа** | Новое обращение |
| **Отвечено** | Менеджер ответил |

---

## 9. Квиз и лиды

Раздел: **Квиз → Заявки с квиза**

Лиды от пользователей, прошедших квиз на сайте.

### Как обработать лид

1. Откройте лид
2. Посмотрите **Ответы пользователя** — там его предпочтения
3. Свяжитесь с клиентом по телефону или Telegram
4. Отметьте статус **Обработан**

---

### Настройка вопросов квиза

Раздел: **Квиз → Вопросы квиза**

Можно менять без разработчика:
- Добавить или удалить вопрос
- Изменить текст вопроса и варианты ответов
- Изменить порядок вопросов

> Если пользователь начинает квиз повторно — его прогресс сбрасывается автоматически.

---

## 10. Отзывы

Собственной базы отзывов в системе нет. Отзывы на сайте показываются через два внешних виджета.

| Виджет | Тип | Как настроить |
|--------|-----|---------------|
| Google Reviews | Elfsight (платный) | Вставить App ID |
| TripAdvisor | Elfsight/внешний виджет | Указать App ID или настройки виджета, если он подключён |

---

### Как подключить Google Reviews (Elfsight)

1. Зарегистрируйтесь на [elfsight.com](https://elfsight.com)
2. Создайте виджет **Google Reviews**
3. Скопируйте **App ID**
4. В Admin: **Настройки сайта → Виджеты отзывов → Elfsight Google Reviews App ID**

---

### Как подключить TripAdvisor

1. Подготовьте виджет через используемый сервис виджетов
2. Скопируйте App ID или настройки, которые нужны фронтенду
3. В Admin: **Настройки сайта → Виджеты отзывов**

---

### Включить или выключить виджеты

**Настройки сайта → переключатель "Виджеты отзывов включены"**

---

## 11. Достопримечательности

Раздел: **Достопримечательности → Достопримечательности**

Места, которые показываются на странице города и в связанных турах.

### Как добавить

1. Выберите **Город**
2. Введите **Название** и **Описание**
3. Загрузите **Главное изображение**
4. В блоке **Галерея** добавьте дополнительные фото
5. В поле **Связанные туры** выберите туры, где посещается это место

---

## 12. Команда

Раздел: **Команда → Сотрудники**

Отображается в разделе "О нас" на сайте.

| Поле | Описание |
|------|----------|
| ФИО | Полное имя |
| Должность | Например: Гид, Менеджер |
| Описание | Краткая биография |
| Фото | Портретное фото |
| Порядок | Позиция в списке (0 = первый) |
| Активен | Показывать ли на сайте |

---

## 13. Переводы RU/EN/ES/FR/DE

Большинство текстовых полей имеют вкладки: **Русский**, **English**, **Español**, **Français**, **Deutsch**.

Чтобы сайт выглядел корректно на всех языках — заполняйте все языковые вкладки.

**Где встречаются переводы:**

- Название и описание тура
- Программа по дням и FAQ
- Страны, города, категории
- Достопримечательности
- Вопросы квиза
- Текст о компании
- Команда

> Если перевод не заполнен, на соответствующей языковой версии может появиться fallback или пустой текст.

---

## 14. FAQ по турам

Раздел: **FAQ → FAQ**

Вопросы и ответы, которые показываются на странице конкретного тура.

- Привязаны к конкретному туру
- Порядок меняется через поле **Порядок**
- Скрыть можно через галочку **Активен**

---

## 15. Частые вопросы

---

**Тур создан, но не отображается на сайте?**

Проверьте что стоит галочка **Активен** у тура.

---

**Клиент не может забронировать — пишет "нет мест"?**

Туры → найдите тур → Даты заезда → проверьте поле **Доступные места**.

---

**Бронирование не подтверждается?**

Откройте бронь и проверьте статус, тур, дату и доступные места. Онлайн-платежей сейчас нет, оплату менеджер обрабатывает физически/вручную.

---

**Не приходят уведомления в Telegram?**

Сообщите разработчику — нужно проверить токен бота и настройки.

---

**Как изменить цену тура?**

Туры → найдите тур → измените поле **Цена** → Сохранить.

> Изменение цены не затронет уже созданные бронирования.

---

**Клиент хочет отменить бронирование?**

- Бронирования → выберите бронь → действие **Отменить выбранные брони**
- Если клиент уже оплатил физически, возврат обрабатывается вручную по правилам компании.

---

**Не работает виджет отзывов?**

1. Проверьте переключатель **Виджеты отзывов включены** в Настройках сайта
2. Если включён — проверьте правильность App ID или настроек внешнего виджета

---

*По техническим вопросам обращайтесь к разработчику.*


---

# Operations checklist

Документ для безопасной эксплуатации production. Не храните здесь пароли, токены, SMTP-ключи и доступы.

## 1. Backend deploy

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

## 2. Frontend deploy

```bash
cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

## 3. Database backup

Создавайте backup перед миграциями и крупными изменениями данных.

Ручной backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

По умолчанию backup хранится в `/var/backups/nomads-area`, старые DB backup старше 14 дней удаляются.

Проверка восстановления backup:

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

Скрипт создаёт временную PostgreSQL базу, восстанавливает dump, проверяет наличие таблиц и удаляет временную базу.

## 4. Media backup

Файлы из `MEDIA_ROOT` нужно бэкапить отдельно от PostgreSQL.

Ручной backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

По умолчанию media backup хранится в `/var/backups/nomads-area`, старые media backup старше 14 дней удаляются.

## 5. Automatic backups

Установить systemd timers:

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Расписание:

- DB backup: каждый день в 03:15
- Media backup: каждый день в 03:35

Проверить timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

## 6. Media storage / CDN

Сейчас media может храниться на сервере. Для роста проекта лучше вынести media в S3-compatible storage + CDN, чтобы сервер не был единственной точкой хранения фотографий и видео.

Backend уже поддерживает opt-in режим. В `.env`:

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

## 7. Error monitoring

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

`SENTRY_TRACES_SAMPLE_RATE=0.0` означает: ошибки отправляются, performance tracing выключен. Если потом понадобится performance monitoring, можно поднять до `0.05` или `0.1`.

## 8. Smoke checks after deploy

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

## 9. Load-test rules

Не запускать массовый POST на production. Он создаёт реальные брони/лиды/уведомления.

Для честного GET-теста:

- запускать нагрузку с отдельной VPS;
- заранее проверить, что throttle не превращает тест в поток `429`;
- мониторить `journalctl`, RAM, CPU, PostgreSQL connections;
- прекращать тест при `5xx`, worker timeout, росте swap или p99 выше 2–3 секунд.

Пример wrk:

```bash
/usr/bin/wrk -t2 -c10 -d30s --latency \
  https://www.nomadsarea.com/api/en/tours/54/
```

## 10. Admin data safety

- Если тур выключен через `Активен`, backend не должен принимать новую бронь на этот тур.
- Достопримечательность должна быть одной записью, связанной с несколькими турами, а не дублями.
- Если меняются вопросы квиза, проверяйте ветвление: выбранная ветка не должна показывать вопросы из другой ветки.


---

# Developer handoff

Этот документ нужен следующему разработчику, чтобы быстро понять текущее состояние проекта, правила работы и критичные места. Не храните здесь секреты, токены, пароли и реальные ключи.

## Repositories and production paths

Backend:

- GitHub: `iskakdev/Nomads_Area`
- Production path: `/root/Nomads_Area`
- Django project path: `/root/Nomads_Area/nomads_area`
- Virtualenv: `/root/Nomads_Area/venv`
- Main service: `nomadsarea`
- Celery service: `nomadsarea-celery`

Frontend:

- GitHub: `kubanych-js/nomads-area`
- Production path: `/root/nomads-area`
- Process manager: PM2
- PM2 process: `nomads-frontend`

Production domain:

- Public site: `https://www.nomadsarea.com`
- Backend API is exposed under `/api/...` through Nginx.

## Current backend stack

- Django 5.2.x
- Django REST Framework
- PostgreSQL
- Redis cache
- Celery
- django-modeltranslation for RU/EN/ES/FR/DE model fields
- django-jazzmin admin
- Optional Sentry, disabled until `SENTRY_DSN` is set
- Optional S3-compatible media storage, disabled until `USE_S3_STORAGE=True`

## Dependency files

There is one canonical backend dependency list:

- `nomads_area/requirements.txt`

The repository-root file exists only as a deploy convenience:

- `requirements.txt` contains `-r nomads_area/requirements.txt`

This allows both commands to work:

```bash
cd /root/Nomads_Area
pip install -r requirements.txt
```

```bash
cd /root/Nomads_Area/nomads_area
pip install -r requirements.txt
```

When adding backend dependencies, update only `nomads_area/requirements.txt`.

## Required production environment

Production env file is on the server:

```bash
/root/Nomads_Area/nomads_area/.env
```

Important variables:

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

`DEBUG` must stay `False` in production. If it becomes `True`, Django can expose debug pages with internal settings and stack traces.

## Health and smoke checks

Public health endpoints:

```bash
curl -fsS https://www.nomadsarea.com/api/healthz/
curl -fsS https://www.nomadsarea.com/api/readyz/
```

Full smoke check:

```bash
cd /root/Nomads_Area
bash scripts/smoke_check.sh
```

Expected output includes:

```text
ru tour detail OK
en tour detail OK
es tour detail OK
fr tour detail OK
de tour detail OK
attractions country filter OK
smoke checks OK
```

## Backend deploy

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

## Frontend deploy

```bash
cd /root/nomads-area
git pull --ff-only origin main

rm -rf .next
pnpm build

pm2 restart nomads-frontend --update-env
pm2 save
```

## Backup and restore

Manual database backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_database.sh
```

Manual media backup:

```bash
cd /root/Nomads_Area
bash scripts/backup_media.sh
```

Install automatic systemd timers:

```bash
cd /root/Nomads_Area
bash scripts/install_backup_timers.sh
```

Default schedule:

- DB backup daily at 03:15
- Media backup daily at 03:35
- Backup retention: 14 days

Check timers:

```bash
systemctl list-timers 'nomads-backup-*' --no-pager
journalctl -u nomads-backup-database.service -n 100 --no-pager
journalctl -u nomads-backup-media.service -n 100 --no-pager
```

Check database restore:

```bash
cd /root/Nomads_Area
bash scripts/restore_database_check.sh /var/backups/nomads-area/db-....dump
```

The restore check creates a temporary PostgreSQL database, restores the dump, validates that public tables exist, then drops the temporary database.

## Optional Sentry setup

Sentry is optional and does nothing until `SENTRY_DSN` is set.

Add to `.env`:

```dotenv
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.0
```

Then:

```bash
sudo systemctl restart nomadsarea
sudo systemctl restart nomadsarea-celery
```

Use `SENTRY_TRACES_SAMPLE_RATE=0.0` initially. It sends errors without performance tracing. Raise to `0.05` or `0.1` only when performance data is needed.

## Optional S3/CDN media setup

S3-compatible storage is optional and disabled by default.

Add to `.env` only when the bucket/CDN is ready:

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

Then:

```bash
cd /root/Nomads_Area/nomads_area
source /root/Nomads_Area/venv/bin/activate
python manage.py check
sudo systemctl restart nomadsarea
```

Do not turn on S3 until media migration is planned. Existing local files will not magically move to S3.

## Important business logic

### Active tours

If a tour is inactive, frontend should stop showing it after cache/revalidation, but backend must also reject booking attempts. Backend validation is the final safety layer.

### Bookings

Booking creation validates:

- tour exists;
- tour is active;
- selected tour date belongs to the selected tour;
- extra services belong to the selected tour;
- group tour seats are available;
- duplicate request fingerprints are handled.

### Attractions

Attraction should be one record connected to many tours, not duplicated per tour.

Correct shape:

```text
Attraction
  ├── private tour A
  ├── group tour B
  └── private tour C
```

Country filtering exists for attractions:

```text
/api/ru/attractions/?country=Казахстан
/api/ru/attractions/?country=Kazakhstan
/api/ru/attractions/?country=<country_id>
```

### Quiz branching

Quiz branching must stop after the selected branch. A selected option with `next_question` should lead only to that branch. Other branches should not appear after a concrete branch has been selected.

## Caching rule

The frontend cache/revalidate policy was intentionally left as-is after the latest discussion. Do not change frontend cache behavior casually.

Backend still protects critical actions. Example: even if a stale frontend page shows an inactive tour, backend must reject booking.

## Known operational gotchas

- `https://www.nomadsarea.com/healthz/` may hit frontend/redirects depending on Nginx. Use `/api/healthz/` and `/api/readyz/` for backend health.
- `/api/not-existing-debug-check/` can be interpreted as a locale route. Use `/api/ru/not-existing-debug-check/` to test a real backend 404.
- `DEBUG=False` must be verified after deploy:

```bash
cd /root/Nomads_Area/nomads_area
grep -n '^DEBUG=' .env
curl -sS -i https://www.nomadsarea.com/api/ru/not-existing-debug-check/ | head -40
```

Expected: `404 Not Found`, no Django traceback page.

- Do not run destructive DB commands on production without a fresh backup.
- Do not run mass POST load tests on production. They create real leads/bookings/notifications.

## Tests

Local/full backend tests:

```bash
cd /home/iskhak/PycharmProjects/Nomads_Area
source .venv/bin/activate
python nomads_area/manage.py test nomads_area_app
```

Expected latest count was 39 tests. If PostgreSQL test DB already exists, Django asks whether to delete it; answer `yes` only for local/test DB.

Non-DB checks:

```bash
python nomads_area/manage.py check
python nomads_area/manage.py makemigrations --check --dry-run
python -m compileall nomads_area/nomads_area nomads_area/nomads_area_app
bash -n scripts/*.sh
```

## GitHub Actions

CI workflow was intentionally not committed because pushing workflow files requires a GitHub token with `workflow` scope. The project owner said they will handle this part.

Do not ask for tokens in chat. If CI is added, use a short-lived token with limited repository permissions and workflow scope, or add the workflow through GitHub UI.


---

# Load testing

Run the generator from a VPS separate from the application server. The test
uses only a read-only tour detail endpoint and treats redirects, throttling and
server errors as failures.

## Production preparation

Configure Django to use the shared Redis cache and temporarily raise only the
anonymous read limit:

```env
CACHE_URL=redis://127.0.0.1:6379/1
CACHE_KEY_PREFIX=nomads-area
API_CACHE_TIMEOUT=60
DRF_ANON_THROTTLE_RATE=1000000/minute
```

Restart Gunicorn and verify that repeated requests return `200`. Do not change
`DRF_FORMS_THROTTLE_RATE`; POST forms are outside this test.

## Run

Install k6 on the load-generator VPS, copy this directory there, then run:

```bash
TARGET_URL=https://www.nomadsarea.com/api/en/tours/54/ \
ALLOW_PRODUCTION=yes \
VUS_LOW=10 \
VUS_HIGH=50 \
./loadtest/run.sh
```

Increase `VUS_HIGH` in separate runs: `10`, `25`, `50`, `100`, pausing at
least 30 seconds between runs. Stop when p99 exceeds 1.5 seconds, any 5xx
appears, workers time out, CPU stays above 90%, swap grows, or PostgreSQL
connections approach their limit.

The JSON summary is saved under `loadtest/results/`.

## Server monitoring

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

After a production test, restore the normal anonymous rate and restart
Gunicorn. Keep the shared Redis cache enabled.
