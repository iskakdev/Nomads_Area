from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from phonenumber_field.modelfields import PhoneNumberField


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
    privacy_policy_url = models.URLField(blank=True, verbose_name="Политика конфиденциальности")

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TeamMember(models.Model):
    full_name = models.CharField(max_length=128, verbose_name="ФИО")
    position = models.CharField(max_length=128, blank=True, verbose_name="Должность")
    description = models.TextField(blank=True, verbose_name="Описание")
    photo = models.ImageField(upload_to="team/", null=True, blank=True, verbose_name="Фото")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Сотрудник"
        verbose_name_plural = "Команда"

    def __str__(self):
        return self.full_name


class Country(models.Model):
    country_image = models.ImageField(upload_to="country_images/", null=True, blank=True, verbose_name="Изображение страны")
    country_name = models.CharField(max_length=64, unique=True, verbose_name="Название страны")
    hero_description = models.TextField(blank=True, default="", verbose_name="Описание для главного блока")
    symbol_image = models.ImageField(upload_to="country_symbols/", null=True, blank=True, verbose_name="Символ страны")

    class Meta:
        ordering = ["country_name"]
        verbose_name = "Страна"
        verbose_name_plural = "Страны"

    def __str__(self):
        return self.country_name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities", verbose_name="Страна")
    city_image = models.ImageField(upload_to="city_images/", null=True, blank=True, verbose_name="Изображение города")
    city_name = models.CharField(max_length=64, verbose_name="Название города")

    class Meta:
        ordering = ["city_name"]
        verbose_name = "Город"
        verbose_name_plural = "Города"
        constraints = [
            models.UniqueConstraint(
                fields=["country", "city_name"],
                name="unique_city_per_country"
            )
        ]

    def __str__(self):
        return self.city_name


class TourCategory(models.Model):
    icon = models.ImageField(upload_to="category_icons/", null=True, blank=True, verbose_name="Иконка")
    name = models.CharField(max_length=64, unique=True, verbose_name="Название категории")

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория тура"
        verbose_name_plural = "Категории туров"

    def __str__(self):
        return self.name


class Tour(models.Model):
    TOUR_TYPE_CHOICES = (
        ("group", "Групповой"),
        ("private", "Приватный"),
    )
    SEASON_CHOICES = (
        ("all_year", "Круглый год"),
        ("warm", "Тёплый сезон"),
        ("winter", "Зима"),
    )
    DIFFICULTY_CHOICES = (
        (1, "Лёгкий"),
        (2, "Средний"),
        (3, "Сложный"),
    )
    CURRENCY_CHOICES = (
        ("KGS", "KGS"),
        ("USD", "USD"),
    )

    title = models.CharField(max_length=128, verbose_name="Название тура")
    tour_type = models.CharField(max_length=16, choices=TOUR_TYPE_CHOICES, verbose_name="Тип тура")
    season = models.CharField(max_length=16, choices=SEASON_CHOICES, default="all_year", verbose_name="Сезон")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="tours", verbose_name="Страна")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="tours", null=True, blank=True, verbose_name="Город")
    categories = models.ManyToManyField(TourCategory, blank=True, related_name="tours", verbose_name="Категории")
    duration_days = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name="Длительность в днях")
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES, default=2, verbose_name="Сложность")
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="USD", verbose_name="Валюта")
    price = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Цена")
    max_people = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(10)], verbose_name="Максимум людей")
    description = models.TextField(validators=[MaxLengthValidator(400)], verbose_name="Описание")
    included = models.TextField(verbose_name="Что включено")
    not_included = models.TextField(blank=True, verbose_name="Что не включено")
    activity_tags = models.JSONField(default=list, blank=True, verbose_name="Теги активности")
    tripadvisor_url = models.URLField(null=True, blank=True, verbose_name="TripAdvisor")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Тур"
        verbose_name_plural = "Туры"
        indexes = [
            models.Index(fields=["tour_type", "is_active"], name="tour_type_active_idx"),
            models.Index(fields=["country", "city"], name="tour_country_city_idx"),
            models.Index(fields=["season", "difficulty"], name="tour_season_diff_idx"),
            models.Index(fields=["price"], name="tour_price_idx"),
        ]

    def __str__(self):
        return f"{self.title} ({self.tour_type})"


class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images", verbose_name="Тур")
    image = models.ImageField(upload_to="tour_images/", verbose_name="Фото")

    class Meta:
        verbose_name = "Фото тура"
        verbose_name_plural = "Фото тура"

    def __str__(self):
        return f"Фото: {self.tour.title}"


class ItineraryDay(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="itinerary", verbose_name="Тур")
    day_number = models.PositiveSmallIntegerField(verbose_name="Номер дня")
    title = models.CharField(max_length=128, verbose_name="Заголовок")
    description = models.TextField(validators=[MaxLengthValidator(200)], verbose_name="Описание")
    image = models.ImageField(upload_to="itinerary/", null=True, blank=True, verbose_name="Изображение")
    tags = models.JSONField(default=list, blank=True, verbose_name="Теги")
    altitude = models.CharField(max_length=64, blank=True, verbose_name="Высота")
    walking_distance = models.CharField(max_length=64, blank=True, verbose_name="Пешая дистанция")
    driving_distance = models.CharField(max_length=64, blank=True, verbose_name="Дистанция на машине")
    accommodation = models.CharField(max_length=128, blank=True, verbose_name="Проживание")

    class Meta:
        ordering = ["day_number"]
        verbose_name = "День маршрута"
        verbose_name_plural = "Маршрут по дням"

    def __str__(self):
        return f"{self.tour.title} - День {self.day_number}"


class TourDate(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="dates", verbose_name="Тур")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    available_spots = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="Доступные места")

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Дата заезда"
        verbose_name_plural = "Даты заезда"
        constraints = [
            models.UniqueConstraint(
                fields=["tour", "start_date"],
                name="unique_tour_start_date"
            ),
            models.CheckConstraint(
                check=Q(end_date__gte=F("start_date")),
                name="tourdate_end_after_start"
            ),
            models.CheckConstraint(
                check=Q(available_spots__lte=10),
                name="tourdate_available_spots_lte_10"
            ),
        ]
        indexes = [
            models.Index(
                fields=["start_date", "available_spots"],
                name="tourdate_start_spots_idx"
            )
        ]

    def clean(self):
        if self.tour_id and self.tour.tour_type != "group":
            raise ValidationError({"tour": "Даты заездов только для групповых туров."})
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Дата окончания не может быть раньше даты начала."})

    def __str__(self):
        return f"{self.tour.title}: {self.start_date}"


class TourPriceTier(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="price_tiers", verbose_name="Тур")
    min_people = models.PositiveSmallIntegerField(verbose_name="Минимум людей")
    max_people = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Максимум людей")
    price_per_person = models.PositiveIntegerField(verbose_name="Цена за человека")

    class Meta:
        ordering = ["min_people"]
        verbose_name = "Цена приватного тура"
        verbose_name_plural = "Цены приватных туров"
        constraints = [
            models.CheckConstraint(
                check=Q(max_people__isnull=True) | Q(max_people__gte=F("min_people")),
                name="tier_max_gte_min_or_null"
            )
        ]

    def clean(self):
        if self.tour_id and self.tour.tour_type != "private":
            raise ValidationError({"tour": "Ценовые тиры только для приватных туров."})
        if self.max_people is not None and self.max_people < self.min_people:
            raise ValidationError({"max_people": "Максимум не может быть меньше минимума."})

    def __str__(self):
        if self.max_people:
            return f"{self.min_people}-{self.max_people} чел - {self.price_per_person}$"
        return f"{self.min_people}+ чел - {self.price_per_person}$"


class ExtraService(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="extra_services", null=True, blank=True, verbose_name="Тур")
    title = models.CharField(max_length=128, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(upload_to="extra_services/", null=True, blank=True, verbose_name="Изображение")
    features = models.JSONField(default=list, blank=True, verbose_name="Особенности")
    price = models.PositiveIntegerField(verbose_name="Цена")
    currency = models.CharField(max_length=3, default="USD", verbose_name="Валюта")
    price_label = models.CharField(max_length=64, default="за 1 день тура", verbose_name="Подпись цены")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Дополнительная услуга"
        verbose_name_plural = "Дополнительные услуги"

    def __str__(self):
        return self.title


class FAQ(models.Model):
    MAX_FAQ_PER_TOUR = 10

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="faqs", null=True, blank=True, verbose_name="Тур")
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"

    def clean(self):
        if not self.tour_id:
            return
        existing = FAQ.objects.filter(tour_id=self.tour_id)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.count() >= self.MAX_FAQ_PER_TOUR:
            raise ValidationError({"tour": f"Максимум {self.MAX_FAQ_PER_TOUR} FAQ для одного тура."})

    def __str__(self):
        return self.question


class TourRoutePoint(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="route_points", verbose_name="Тур")
    title = models.CharField(max_length=128, blank=True, verbose_name="Название точки")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name="Долгота")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order"]
        verbose_name = "Точка маршрута"
        verbose_name_plural = "Точки маршрута"

    def __str__(self):
        return self.title


class Booking(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    STATUS_CHOICES = (
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждён"),
        ("cancelled", "Отменён"),
        ("rejected", "Отклонён"),
    )

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="bookings", verbose_name="Тур")
    tour_date = models.ForeignKey(TourDate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Дата тура")
    preferred_start_date = models.DateField(null=True, blank=True, verbose_name="Желаемая дата начала")
    preferred_end_date = models.DateField(null=True, blank=True, verbose_name="Желаемая дата окончания")
    customer_name = models.CharField(max_length=128, verbose_name="Имя клиента")
    customer_contact = models.CharField(max_length=128, default="", verbose_name="Контакт клиента")
    people_details = models.CharField(max_length=255, blank=True, default="", verbose_name="Состав группы")
    comment = models.TextField(blank=True, default="", verbose_name="Комментарий")
    adults = models.PositiveSmallIntegerField(default=1, verbose_name="Взрослые")
    children = models.PositiveSmallIntegerField(default=0, verbose_name="Дети")
    number_of_people = models.PositiveSmallIntegerField(verbose_name="Количество людей")
    price_per_person = models.PositiveIntegerField(verbose_name="Цена за человека")
    total_price = models.PositiveIntegerField(verbose_name="Итоговая цена")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        indexes = [
            models.Index(fields=["status", "created_at"], name="booking_status_created_idx"),
            models.Index(fields=["tour", "created_at"], name="booking_tour_created_idx"),
            models.Index(fields=["customer_contact", "created_at"], name="booking_contact_created_idx"),
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.tour.title}"


class Payment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Ожидает оплаты"),
        ("paid", "Оплачен"),
        ("failed", "Ошибка оплаты"),
        ("cancelled", "Отменён"),
    )

    PROVIDER_CHOICES = (
        ("finikpay", "FinikPay"),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment", verbose_name="Бронирование")
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default="finikpay", verbose_name="Платёжная система")
    amount = models.PositiveIntegerField(verbose_name="Сумма")
    currency = models.CharField(max_length=3, default="USD", verbose_name="Валюта")
    external_payment_id = models.CharField(max_length=128, blank=True, default="", verbose_name="ID платежа во внешней системе")
    payment_url = models.URLField(blank=True, default="", verbose_name="Ссылка на оплату")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата оплаты")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        indexes = [
            models.Index(fields=["status", "created_at"], name="payment_status_created_idx"),
            models.Index(fields=["external_payment_id"], name="payment_external_id_idx"),
        ]

    def __str__(self):
        return f"{self.booking_id} - {self.amount} {self.currency} - {self.status}"


class QuizQuestion(models.Model):
    QUESTION_TYPE_CHOICES = (
        ("radio", "Один ответ"),
        ("checkbox", "Несколько ответов"),
        ("text", "Текст"),
    )

    text = models.CharField(max_length=255, verbose_name="Вопрос")
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPE_CHOICES, default="radio", verbose_name="Тип вопроса")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ["order"]
        verbose_name = "Вопрос квиза"
        verbose_name_plural = "Вопросы квиза"
        indexes = [
            models.Index(fields=["is_active", "order"], name="quizq_active_order_idx")
        ]

    def __str__(self):
        return self.text


class QuizAnswerOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options", verbose_name="Вопрос")
    text = models.CharField(max_length=255, verbose_name="Текст ответа")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ["order"]
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"

    def __str__(self):
        return self.text


class QuizLead(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    name = models.CharField(max_length=64, blank=True, default="", verbose_name="Имя")
    phone_or_telegram = models.CharField(max_length=64, blank=True, default="", verbose_name="Телефон или Telegram")
    answers = models.JSONField(verbose_name="Ответы")
    is_processed = models.BooleanField(default=False, verbose_name="Обработан")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Заявка с квиза"
        verbose_name_plural = "Заявки с квиза"

    def __str__(self):
        return f"Квиз: {self.name} - {self.created_at:%Y-%m-%d}"


class QuizProgress(models.Model):
    session_key = models.CharField(max_length=64, unique=True, verbose_name="Ключ сессии")
    answers = models.JSONField(default=dict, verbose_name="Ответы")
    current_question_index = models.PositiveSmallIntegerField(default=0, verbose_name="Текущий вопрос")
    is_completed = models.BooleanField(default=False, verbose_name="Завершён")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Прогресс квиза"
        verbose_name_plural = "Прогресс квизов"
        indexes = [
            models.Index(fields=["session_key", "is_completed"], name="quizprogress_session_done_idx")
        ]

    def __str__(self):
        return f"Прогресс: {self.session_key}"


class Attraction(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="attractions", verbose_name="Город")
    name = models.CharField(max_length=128, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    image = models.ImageField(upload_to="attractions/", null=True, blank=True, verbose_name="Главное изображение")
    tours = models.ManyToManyField(Tour, blank=True, related_name="attractions", verbose_name="Связанные туры")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        ordering = ["name"]
        verbose_name = "Достопримечательность"
        verbose_name_plural = "Достопримечательности"
        indexes = [
            models.Index(fields=["city", "is_active"], name="attraction_city_active_idx")
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class AttractionImage(models.Model):
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name="images", verbose_name="Достопримечательность")
    image = models.ImageField(upload_to="attraction_images/", verbose_name="Фото")

    class Meta:
        verbose_name = "Фото достопримечательности"
        verbose_name_plural = "Фото достопримечательностей"

    def __str__(self):
        return f"Фото: {self.attraction.name}"


class TransferRoute(models.Model):
    departure_point = models.CharField(max_length=128, verbose_name="Откуда")
    arrival_point = models.CharField(max_length=128, verbose_name="Куда")
    distance_km = models.PositiveIntegerField(verbose_name="Расстояние, км")

    class Meta:
        ordering = ["departure_point", "arrival_point"]
        verbose_name = "Маршрут трансфера"
        verbose_name_plural = "Маршруты трансфера"
        constraints = [
            models.UniqueConstraint(
                fields=["departure_point", "arrival_point"],
                name="unique_transfer_route_points"
            )
        ]

    def __str__(self):
        return f"{self.departure_point} -> {self.arrival_point}"


class VehicleType(models.Model):
    VEHICLE_CATEGORY_CHOICES = (
        ("sedan", "Седан"),
        ("minivan", "Минивэн"),
        ("minibus", "Миниавтобус"),
    )

    route = models.ForeignKey(TransferRoute, on_delete=models.CASCADE, related_name="vehicles", verbose_name="Маршрут")
    category = models.CharField(max_length=16, choices=VEHICLE_CATEGORY_CHOICES, verbose_name="Категория машины")
    price = models.PositiveIntegerField(verbose_name="Цена")
    seats = models.PositiveSmallIntegerField(verbose_name="Количество мест")
    bags = models.PositiveSmallIntegerField(verbose_name="Количество мест для багажа")

    class Meta:
        ordering = ["route_id", "category"]
        verbose_name = "Тип машины"
        verbose_name_plural = "Типы машин"
        constraints = [
            models.UniqueConstraint(
                fields=["route", "category"],
                name="unique_vehicle_category_per_route"
            )
        ]

    def __str__(self):
        return f"{self.get_category_display()} - {self.price}$"


class TransportRequest(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    STATUS_CHOICES = (
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждён"),
        ("cancelled", "Отменён"),
        ("rejected", "Отклонён"),
    )

    vehicle = models.ForeignKey(VehicleType, on_delete=models.CASCADE, verbose_name="Машина")
    travel_date = models.DateField(null=True, blank=True, verbose_name="Дата поездки")
    flight_number = models.CharField(max_length=32, blank=True, default="", verbose_name="Номер рейса")
    customer_name = models.CharField(max_length=128, blank=True, default="", verbose_name="Имя клиента")
    customer_phone = PhoneNumberField(verbose_name="Телефон клиента")
    passengers = models.PositiveSmallIntegerField(default=1, verbose_name="Пассажиры")
    luggage_count = models.PositiveSmallIntegerField(default=0, verbose_name="Количество багажа")
    total_price = models.PositiveIntegerField(verbose_name="Итоговая цена")
    comment = models.TextField(blank=True, default="", verbose_name="Комментарий")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка на трансфер"
        verbose_name_plural = "Заявки на трансфер"
        indexes = [
            models.Index(fields=["status", "created_at"], name="transport_status_created_idx"),
            models.Index(fields=["customer_phone", "created_at"], name="transport_phone_created_idx"),
        ]

    def __str__(self):
        return f"{self.customer_phone} - {self.vehicle}"


class ContactRequest(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    STATUS_CHOICES = (
        ("pending", "Ожидает ответа"),
        ("answered", "Отвечено"),
    )

    name = models.CharField(max_length=128, verbose_name="Имя")
    phone_or_email = models.CharField(max_length=128, verbose_name="Телефон или Email")
    message = models.TextField(verbose_name="Сообщение")
    subject = models.CharField(max_length=256, blank=True, default="", verbose_name="Тема")
    source = models.CharField(max_length=64, blank=True, default="", verbose_name="Источник")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending", verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Контактная заявка"
        verbose_name_plural = "Контактные заявки"
        indexes = [
            models.Index(fields=["status", "created_at"], name="contact_status_created_idx"),
            models.Index(fields=["source", "created_at"], name="contact_source_created_idx"),
            models.Index(fields=["phone_or_email", "created_at"], name="contact_email_created_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.subject or self.source}"
