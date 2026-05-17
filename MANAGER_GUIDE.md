# Руководство для менеджера Nomads Area

---

## 1. Вход в админ-панель

Адрес:

`https://api.nomads-area.com/admin/`

(после деплоя)

Локально:

`http://127.0.0.1:8000/admin/`

Логин и пароль предоставляются разработчиком.

---

## 2. Настройки сайта

Перед началом работы заполните **Site Settings**:

- Телефон, WhatsApp, Email
- Соцсети (Instagram, Facebook, YouTube, TikTok)
- Tripadvisor URL
- Текст "О нас", статистика (лет опыта, туристов, маршрутов)

---

## 3. Добавление страны

1. **Countries** -> **Add country**.
2. Заполните:
   - `country_name` - название страны
   - `country_image` - главное фото страны
   - `hero_description` - описание для баннера
   - `symbol_image` - символ страны
3. Нажмите **Save**.

---

## 4. Добавление города

1. **Cities** -> **Add city**.
2. Выберите страну.
3. Заполните:
   - `city_name`
   - `city_image`
4. Нажмите **Save**.

---

## 5. Добавление тура (главное)

### Шаг 1. Создать тур

1. **Tours** -> **Add tour**.
2. Заполните основные поля:

- `title` - название тура
- `tour_type` - **group** или **private**
- `country`, `city`
- `categories` - категории тура
- `season`
- `duration_days` - количество дней
- `difficulty` - сложность
- `max_people`
- `price` - базовая цена
- `currency`
- `description`
- `included`
- `not_included`
- `activity_tags`

---

### Шаг 2. Для GROUP тура - добавить даты

В блоке **Tour Dates**:

- `start_date`
- `end_date`
- `available_spots`

⚠️ Места уменьшаются автоматически после бронирования.

---

### Шаг 3. Для PRIVATE тура - добавить Price Tiers

В блоке **Tour Price Tiers**:

- `min_people`
- `max_people`
- `price_per_person`

Пример:

| min_people | max_people | price_per_person |
|---|---|---|
| 1 | 2 | 250 |
| 3 | 5 | 200 |
| 6 |  | 180 |

---

### Шаг 4. Добавить программу тура

В блоке **Itinerary Days**:

- `day_number`
- `title`
- `description`
- `image`
- `tags`
- `altitude`
- `walking_distance`
- `driving_distance`
- `accommodation`

---

### Шаг 5. Добавить фотографии

В блоке **Tour Images** загрузите несколько фото.

⚠️ Первая фотография используется как обложка тура.

---

### Шаг 6. Добавить FAQ

В блоке **FAQs**:

- `question`
- `answer`

Максимум: **10 FAQ** на один тур.

---

### Шаг 7. Дополнительные услуги

В блоке **Extra Services**:

- аренда лошади
- спальник
- VIP трансфер
- отдельный номер
- фотосъёмка

Поля:

- `title`
- `description`
- `image`
- `features`
- `price`
- `currency`
- `price_label`

---

### Шаг 8. Точки маршрута

В блоке **Tour Route Points**:

- `title`
- `latitude`
- `longitude`
- `order`

---

### Шаг 9. Нажать Save

---

## 6. Бронирования

### Bookings

Все новые заявки создаются со статусом:

`pending`

После связи с клиентом измените статус:

- `confirmed`
- `cancelled`
- `rejected`

⚠️ Важно:

Если GROUP бронирование отменяется,
места нужно вернуть вручную в **Tour Dates**.

---

## 7. Оплаты

### Payments

Статусы:

- `pending`
- `paid`
- `failed`
- `refunded`

Пока FinikPay подключён не полностью,
статус можно менять вручную.

---

## 8. Достопримечательности

### Attractions

Поля:

- `city`
- `name`
- `description`
- `image`
- `tours`
- `is_active`

---

## 9. Трансферы

### Transfer Routes

Создайте маршрут:

- `departure_point`
- `arrival_point`
- `distance_km`

---

### Vehicle Types

Для каждого маршрута добавьте машины:

- `category`
- `price`
- `seats`
- `bags`

Типы машин:

- `sedan`
- `minivan`
- `minibus`

---

## 10. Заявки на трансфер

### Transport Requests

Статусы:

- `pending`
- `confirmed`
- `cancelled`
- `completed`

---

## 11. Контактные заявки

### Contact Requests

Источники:

- `contact_form`
- `footer_form`
- `whatsapp_widget`
- `consultation`

После ответа клиенту:

`status = answered`

---

## 12. Команда

### Team Members

Поля:

- `full_name`
- `position`
- `description`
- `photo`
- `order`
- `is_active`

⚠️ `order` влияет на порядок отображения.

---

## 13. Квиз

### Quiz Questions

Поля:

- `text`
- `question_type`
- `order`
- `is_active`

---

### Quiz Answer Options

Поля:

- `text`
- `order`

---

## 14. Заявки квиза

### Quiz Leads

После обработки:

`is_processed = True`

---

## 15. Уведомления

Все новые заявки автоматически отправляются:

- Telegram
- Email

Типы уведомлений:

- бронирования
- контактные формы
- трансферы
- квиз

---

## 16. Мультиязычность

Сайт поддерживает:

- русский
- английский

В админке будут вкладки:

`RU | EN`

Заполняйте оба языка.

---

## 17. Важные правила

Не удаляйте:

- страны с турами
- города с турами
- даты туров с бронированиями

Перед публикацией тура проверьте:

- фото
- даты
- FAQ
- описание
- цену
- маршруты
- количество мест

---

## 18. Контакты разработчика

Telegram: `@iskhak_dev`

Email: `eshmatoviskak@gmail.com`
