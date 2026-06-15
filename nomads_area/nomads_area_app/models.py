from decimal import Decimal
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class SiteSettings(models.Model):
    phone = models.CharField(max_length=32, blank=True, verbose_name="Телефон")
    whatsapp = models.CharField(max_length=32, blank=True, verbose_name="WhatsApp")
    email = models.EmailField(blank=True, verbose_name="Email")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook")
    youtube_url = models.URLField(blank=True, verbose_name="YouTube")
    tiktok_url = models.URLField(blank=True, verbose_name="TikTok")
    tripadvisor_url = models.URLField(blank=True, verbose_name="TripAdvisor")
    about_text = models.TextField(blank=True, verbose_name="Текст о компании")
    about_video_url = models.URLField(blank=True, verbose_name="Видео о компании")
    years_experience = models.PositiveSmallIntegerField(default=5, verbose_name="Лет опыта")
    tourists_count = models.PositiveIntegerField(default=1200, verbose_name="Количество туристов")
    routes_count = models.PositiveSmallIntegerField(default=40, verbose_name="Количество маршрутов")
    reviews_enabled = models.BooleanField(default=False, verbose_name="Виджеты отзывов включены")
    elfsight_google_reviews_app_id = models.CharField(max_length=128, blank=True, verbose_name="Elfsight Google Reviews App ID")
    privacy_policy = models.TextField(blank=True, verbose_name="Политика конфиденциальности")

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки системы"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TeamMember(models.Model):
    full_name = models.CharField(max_length=128, verbose_name="Полное имя")
    position = models.CharField(max_length=128, verbose_name="Должность")
    description = models.TextField(blank=True, verbose_name="Описание")
    photo = models.ImageField(upload_to="team/", verbose_name="Фотография")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Член команды"
        verbose_name_plural = "Команда"

    def __str__(self):
        return self.full_name


class Country(models.Model):
    country_name = models.CharField(max_length=64, unique=True, verbose_name="Название страны")
    country_image = models.ImageField(upload_to="countries/", verbose_name="Изображение страны")
    hero_description = models.TextField(blank=True, verbose_name="Описание для Hero")
    symbol_image = models.ImageField(upload_to="countries/symbols/", blank=True, null=True, verbose_name="Символ")

    class Meta:
        ordering = ["country_name"]
        verbose_name = "Страна"
        verbose_name_plural = "Страны"

    def __str__(self):
        return self.country_name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities", verbose_name="Страна")
    city_name = models.CharField(max_length=64, verbose_name="Название города")
    city_image = models.ImageField(upload_to="cities/", verbose_name="Изображение города")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        ordering = ["city_name"]
        verbose_name = "Город"
        verbose_name_plural = "Города"
        constraints = [models.UniqueConstraint(fields=["country", "city_name"], name="unique_city_per_country")]

    def __str__(self):
        return f"{self.city_name} ({self.country.country_name})"


class TourCategory(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name="Название категории")
    image = models.ImageField(upload_to="categories/", verbose_name="Изображение")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Tour(models.Model):
    TOUR_TYPE_GROUP = "group"
    TOUR_TYPE_PRIVATE = "private"
    SEASON_ALL_YEAR = "all_year"
    SEASON_WARM = "warm"
    SEASON_WINTER = "winter"

    TOUR_TYPE_CHOICES = ((TOUR_TYPE_GROUP, "Групповой"), (TOUR_TYPE_PRIVATE, "Приватный"))
    SEASON_CHOICES = ((SEASON_ALL_YEAR, "Круглый год"), (SEASON_WARM, "Тёплый"), (SEASON_WINTER, "Зима"))

    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="tours", verbose_name="Страна")
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="tours", verbose_name="Город")
    categories = models.ManyToManyField(TourCategory, related_name="tours", verbose_name="Категории")
    title = models.CharField(max_length=256, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    tour_type = models.CharField(max_length=16, choices=TOUR_TYPE_CHOICES, default=TOUR_TYPE_GROUP, verbose_name="Тип")
    season = models.CharField(max_length=16, choices=SEASON_CHOICES, default=SEASON_ALL_YEAR, verbose_name="Сезон")
    duration_days = models.PositiveSmallIntegerField(verbose_name="Длительность")
    difficulty = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(3)], verbose_name="Сложность")
    price = models.PositiveIntegerField(verbose_name="Базовая цена")
    currency = models.CharField(max_length=8, default="USD", verbose_name="Валюта")
    max_group_size = models.PositiveIntegerField(default=10, verbose_name="Макс. мест")
    included = models.TextField(blank=True, verbose_name="Включено")
    not_included = models.TextField(blank=True, verbose_name="Не включено")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Тур"
        verbose_name_plural = "Туры"
        indexes = [
            models.Index(fields=["tour_type", "is_active"], name="tour_type_active_idx"),
            models.Index(fields=["country", "is_active"], name="tour_country_active_idx"),
        ]

    def __str__(self):
        return self.title


class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images", verbose_name="Тур")
    image = models.ImageField(upload_to="tours/", verbose_name="Изображение")
    alt_text = models.CharField(max_length=160, blank=True, verbose_name="Alt")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Изображение"
        verbose_name_plural = "Изображения"

    def __str__(self):
        return f"Фото {self.tour.title}"


class ItineraryDay(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="itinerary_days", verbose_name="Тур")
    day_number = models.PositiveSmallIntegerField(verbose_name="День")
    title = models.CharField(max_length=256, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to="itinerary/", blank=True, null=True, verbose_name="Фото")
    altitude = models.CharField(max_length=64, blank=True, verbose_name="Высота")
    walking_distance = models.CharField(max_length=64, blank=True, verbose_name="Пешком")
    driving_distance = models.CharField(max_length=64, blank=True, verbose_name="На авто")
    accommodation = models.CharField(max_length=128, blank=True, verbose_name="Проживание")

    class Meta:
        ordering = ["day_number"]
        verbose_name = "День маршрута"
        verbose_name_plural = "Дни"
        constraints = [models.UniqueConstraint(fields=["tour", "day_number"], name="unique_itinerary_day")]

    def __str__(self):
        return f"День {self.day_number}: {self.title}"


class TourDate(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="dates", verbose_name="Тур")
    start_date = models.DateField(verbose_name="Начало")
    end_date = models.DateField(verbose_name="Окончание")
    available_spots = models.PositiveIntegerField(verbose_name="Места")

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Дата"
        verbose_name_plural = "Даты"
        indexes = [models.Index(fields=["start_date", "available_spots"], name="tour_date_lookup_idx")]

    def __str__(self):
        return f"{self.tour.title} ({self.start_date})"

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Дата начала позже окончания")


class TourPriceTier(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="price_tiers", verbose_name="Тур")
    min_people = models.PositiveSmallIntegerField(verbose_name="Мин. чел")
    max_people = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Макс. чел")
    price_per_person = models.PositiveIntegerField(verbose_name="Цена за чел")

    class Meta:
        ordering = ["min_people"]
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def __str__(self):
        return f"{self.min_people}-{self.max_people or 'inf'} чел: {self.price_per_person}"

    def clean(self):
        if self.max_people and self.min_people > self.max_people:
            raise ValidationError("Мин > Макс")


class FAQ(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="faqs", verbose_name="Тур")
    question = models.CharField(max_length=256, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"

    def __str__(self):
        return self.question


class ExtraService(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="extra_services", verbose_name="Тур")
    title = models.CharField(max_length=128, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to="services/", blank=True, null=True, verbose_name="Фото")
    features = ArrayField(models.CharField(max_length=64), blank=True, default=list, verbose_name="Фичи")
    price = models.PositiveIntegerField(verbose_name="Цена")
    currency = models.CharField(max_length=8, default="USD", verbose_name="Валюта")
    price_label = models.CharField(max_length=64, blank=True, verbose_name="Метка")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return self.title


class TourRoutePoint(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="route_points", verbose_name="Тур")
    title = models.CharField(max_length=128, verbose_name="Название")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Долгота")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Точка"
        verbose_name_plural = "Точки"

    def __str__(self):
        return self.title


class Attraction(models.Model):
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="attractions", verbose_name="Город")
    tours = models.ManyToManyField(Tour, related_name="attractions", blank=True, verbose_name="Туры")
    name = models.CharField(max_length=128, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to="attractions/", verbose_name="Фото")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        ordering = ["name"]
        verbose_name = "Достопримечательность"
        verbose_name_plural = "Достопримечательности"

    def __str__(self):
        return self.name


class AttractionImage(models.Model):
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name="images", verbose_name="Место")
    image = models.ImageField(upload_to="attractions/gallery/", verbose_name="Фото")
    alt_text = models.CharField(max_length=160, blank=True, verbose_name="Alt")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Фото места"
        verbose_name_plural = "Галерея"


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Ожидает"),
        (STATUS_CONFIRMED, "Подтверждено"),
        (STATUS_CANCELLED, "Отменено"),
        (STATUS_REJECTED, "Отклонено"),
    )

    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name="bookings", verbose_name="Тур")
    tour_date = models.ForeignKey(TourDate, on_delete=models.PROTECT, null=True, blank=True, related_name="bookings", verbose_name="Дата")
    preferred_start_date = models.DateField(null=True, blank=True, verbose_name="Желаемое начало")
    preferred_end_date = models.DateField(null=True, blank=True, verbose_name="Желаемое окончание")
    customer_name = models.CharField(max_length=128, verbose_name="Имя")
    customer_contact = models.CharField(max_length=128, verbose_name="Контакт")
    adults = models.PositiveSmallIntegerField(default=1, verbose_name="Взрослые")
    children = models.PositiveSmallIntegerField(default=0, verbose_name="Дети")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Цена за чел")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итого")
    prepayment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), verbose_name="Предоплата")
    currency = models.CharField(max_length=8, default="USD", verbose_name="Валюта")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="Статус")
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name="Подтверждено")
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="Отменено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    dedup_hash = models.CharField(max_length=64, unique=True, db_index=True, editable=False, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Бронь"
        verbose_name_plural = "Бронирования"

    def __str__(self):
        return f"Бронь #{self.id}"

    @property
    def number_of_people(self):
        return self.adults + self.children

    @property
    def is_group_booking(self):
        return self.tour.tour_type == Tour.TOUR_TYPE_GROUP

    def confirm_and_reserve(self, locked_booking=None):
        booking = locked_booking or Booking.objects.select_for_update().select_related("tour", "tour_date").get(pk=self.pk)
        if booking.status == Booking.STATUS_CONFIRMED:
            return booking
        if booking.status != Booking.STATUS_PENDING:
            raise ValidationError(f"Нельзя подтвердить '{booking.status}'")

        if booking.is_group_booking and booking.tour_date_id:
            tour_date = TourDate.objects.select_for_update().get(pk=booking.tour_date_id)
            if booking.number_of_people > tour_date.available_spots:
                raise ValidationError(f"Мест: {tour_date.available_spots}")
            tour_date.available_spots -= booking.number_of_people
            tour_date.save(update_fields=["available_spots"])

        booking.status = Booking.STATUS_CONFIRMED
        booking.confirmed_at = timezone.now()
        booking.save(update_fields=["status", "confirmed_at"])
        return booking

    def cancel(self):
        if self.status == Booking.STATUS_CANCELLED:
            return self
        if self.status == Booking.STATUS_CONFIRMED and self.payments.filter(status=Payment.STATUS_PAID).exists():
            raise ValidationError("Нельзя отменить оплаченную бронь.")
        self.status = Booking.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at"])
        return self


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    PROVIDER_FINIKPAY = "finikpay"
    PROVIDER_MANUAL = "manual"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Ожидает"), (STATUS_PAID, "Оплачено"),
        (STATUS_FAILED, "Ошибка"), (STATUS_REFUNDED, "Возврат"),
    )
    PROVIDER_CHOICES = ((PROVIDER_FINIKPAY, "FinikPay"), (PROVIDER_MANUAL, "Ручной"))

    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments", verbose_name="Бронь")
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default=PROVIDER_FINIKPAY, verbose_name="Провайдер")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    currency = models.CharField(max_length=8, default="USD", verbose_name="Валюта")
    provider_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True, verbose_name="ID провайдера")
    payment_url = models.URLField(max_length=512, blank=True, default="", verbose_name="Ссылка")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="Статус")
    provider_payload = models.JSONField(default=dict, blank=True, verbose_name="Payload")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Оплачено")
    failed_at = models.DateTimeField(null=True, blank=True, verbose_name="Ошибка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        indexes = [models.Index(fields=["provider", "provider_payment_id"], name="payment_provider_idx")]

    def __str__(self):
        return f"Платёж #{self.id}"

    def mark_paid_and_confirm_booking(self, provider_payload=None):
        provider_payload = provider_payload or {}
        with transaction.atomic():
            payment = Payment.objects.select_for_update().select_related("booking", "booking__tour", "booking__tour_date").get(pk=self.pk)
            if payment.status == Payment.STATUS_PAID:
                return payment, False
            if payment.status != Payment.STATUS_PENDING:
                raise ValidationError(f"Статус '{payment.status}'")

            payment.booking.confirm_and_reserve(locked_booking=payment.booking)
            payment.status = Payment.STATUS_PAID
            payment.paid_at = timezone.now()
            payment.provider_payload = provider_payload
            payment.save(update_fields=["status", "paid_at", "provider_payload", "updated_at"])
            return payment, True

    def mark_failed(self, provider_payload=None):
        if self.status == Payment.STATUS_FAILED:
            return self
        self.status = Payment.STATUS_FAILED
        self.failed_at = timezone.now()
        self.provider_payload = provider_payload or {}
        self.save(update_fields=["status", "failed_at", "provider_payload", "updated_at"])
        return self


class QuizQuestion(models.Model):
    QUESTION_TYPE_CHOICES = (("single", "Один"), ("multiple", "Несколько"), ("text", "Текст"))
    question_text = models.CharField(max_length=256, verbose_name="Вопрос")
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPE_CHOICES, default="single", verbose_name="Тип")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Вопрос квиза"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.question_text


class QuizAnswerOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options", verbose_name="Вопрос")
    option_text = models.CharField(max_length=256, default="", verbose_name="Вариант")
    next_question = models.ForeignKey(QuizQuestion, on_delete=models.SET_NULL, null=True, blank=True, related_name="triggered_by_options", verbose_name="Следующий")

    class Meta:
        verbose_name = "Вариант"
        verbose_name_plural = "Варианты"

    def __str__(self):
        return self.option_text


class QuizLead(models.Model):
    STATUS_CHOICES = (("pending", "Новый"), ("processed", "Обработан"))
    customer_name = models.CharField(max_length=128, default="", verbose_name="Имя")
    customer_contact = models.CharField(max_length=128, default="", verbose_name="Контакт")
    answers_data = models.JSONField(default=dict, verbose_name="Ответы")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Лид"
        verbose_name_plural = "Лиды"

    def __str__(self):
        return f"Лид #{self.id}"


class QuizProgress(models.Model):
    session_key = models.CharField(max_length=256, unique=True, verbose_name="Сессия")
    answers_data = models.JSONField(default=dict, verbose_name="Ответы")
    current_question_index = models.PositiveSmallIntegerField(default=0, verbose_name="Текущий вопрос")
    is_completed = models.BooleanField(default=False, verbose_name="Завершен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлён")

    class Meta:
        verbose_name = "Прогресс квиза"
        verbose_name_plural = "Прогрессы"

    def __str__(self):
        return f"Сессия {self.session_key}"


class TransferRoute(models.Model):
    departure_point = models.CharField(max_length=128, verbose_name="Откуда")
    arrival_point = models.CharField(max_length=128, verbose_name="Куда")

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"
        constraints = [models.UniqueConstraint(fields=["departure_point", "arrival_point"], name="unique_transfer")]

    def __str__(self):
        return f"{self.departure_point} -> {self.arrival_point}"


class VehicleType(models.Model):
    CATEGORY_CHOICES = (("sedan", "Седан"), ("minivan", "Минивэн"), ("minibus", "Миниавтобус"))
    route = models.ForeignKey(TransferRoute, on_delete=models.CASCADE, related_name="vehicles", verbose_name="Маршрут")
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES, verbose_name="Тип")
    price = models.PositiveIntegerField(verbose_name="Цена")
    seats = models.PositiveSmallIntegerField(verbose_name="Места")
    bags = models.PositiveSmallIntegerField(verbose_name="Багаж")

    class Meta:
        verbose_name = "Авто"
        verbose_name_plural = "Авто"
        constraints = [models.UniqueConstraint(fields=["route", "category"], name="unique_vehicle_category")]

    def __str__(self):
        return f"{self.get_category_display()} на {self.route}"


class TransportRequest(models.Model):
    STATUS_CHOICES = (("pending", "Ожидает"), ("confirmed", "Подтверждено"), ("cancelled", "Отменено"))
    vehicle = models.ForeignKey(VehicleType, on_delete=models.PROTECT, related_name="requests", verbose_name="Авто")
    customer_name = models.CharField(max_length=128, blank=True, default="", verbose_name="Имя")
    customer_phone = models.CharField(max_length=32, verbose_name="Телефон")
    comment = models.TextField(blank=True, default="", verbose_name="Комментарий")
    total_price = models.PositiveIntegerField(verbose_name="Цена")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка на трансфер"
        verbose_name_plural = "Заявки"
        indexes = [models.Index(fields=["customer_phone", "created_at"], name="transport_phone_idx")]

    def __str__(self):
        return f"{self.customer_phone} - {self.vehicle}"


class ContactRequest(models.Model):
    STATUS_CHOICES = (("pending", "Ожидает"), ("answered", "Отвечено"))
    name = models.CharField(max_length=128, verbose_name="Имя")
    phone_or_email = models.CharField(max_length=128, verbose_name="Контакт")
    message = models.TextField(verbose_name="Сообщение")
    subject = models.CharField(max_length=256, blank=True, default="", verbose_name="Тема")
    source = models.CharField(max_length=64, blank=True, default="", verbose_name="Источник")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        return f"Заявка #{self.id}"

