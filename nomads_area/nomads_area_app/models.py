from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from phonenumber_field.modelfields import PhoneNumberField

# ========================
# SITE SETTINGS
# ========================

class SiteSettings(models.Model):
    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    tripadvisor_url = models.URLField(blank=True)
    about_text = models.TextField(blank=True)
    about_video_url = models.URLField(blank=True)
    years_experience = models.PositiveSmallIntegerField(default=5)
    tourists_count = models.PositiveIntegerField(default=1200)
    routes_count = models.PositiveSmallIntegerField(default=40)
    privacy_policy_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

# ========================
# TEAM
# ========================

class TeamMember(models.Model):
    full_name = models.CharField(max_length=128)
    position = models.CharField(max_length=128, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="team/", null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.full_name

# ========================
# COUNTRY & CITY
# ========================

class Country(models.Model):
    country_image = models.ImageField(upload_to="country_images/", null=True, blank=True)
    country_name = models.CharField(max_length=64, unique=True)
    hero_description = models.TextField(blank=True, default="")
    symbol_image = models.ImageField(upload_to="country_symbols/", null=True, blank=True)

    class Meta:
        ordering = ["country_name"]

    def __str__(self):
        return self.country_name


class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities")
    city_image = models.ImageField(upload_to="city_images/", null=True, blank=True)
    city_name = models.CharField(max_length=64)

    class Meta:
        ordering = ["city_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["country", "city_name"],
                name="unique_city_per_country"
            )
        ]

    def __str__(self):
        return self.city_name

# ========================
# TOUR
# ========================

class TourCategory(models.Model):
    icon = models.ImageField(upload_to="category_icons/", null=True, blank=True)
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tour(models.Model):
    TOUR_TYPE_CHOICES = (
        ("group", "Групповой"),
        ("private", "Приватный")
    )
    SEASON_CHOICES = (
        ("all_year", "Круглый год"),
        ("warm", "Тёплый сезон"),
        ("winter", "Зима")
    )
    DIFFICULTY_CHOICES = ((1, "Лёгкий"), (2, "Средний"), (3, "Сложный"))
    CURRENCY_CHOICES = (("KGS", "KGS"), ("USD", "USD"))

    title = models.CharField(max_length=128)
    tour_type = models.CharField(max_length=16, choices=TOUR_TYPE_CHOICES)
    season = models.CharField(max_length=16, choices=SEASON_CHOICES, default="all_year")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="tours")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="tours", null=True, blank=True)
    categories = models.ManyToManyField(TourCategory, blank=True, related_name="tours")
    duration_days = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES, default=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="USD")
    price = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    max_people = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(10)])
    description = models.TextField(validators=[MaxLengthValidator(400)])
    included = models.TextField()
    not_included = models.TextField(blank=True)
    activity_tags = models.JSONField(default=list, blank=True)
    tripadvisor_url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tour_type", "is_active"], name="tour_type_active_idx"),
            models.Index(fields=["country", "city"], name="tour_country_city_idx"),
            models.Index(fields=["season", "difficulty"], name="tour_season_diff_idx"),
            models.Index(fields=["price"], name="tour_price_idx")
        ]

    def __str__(self):
        return f"{self.title} ({self.tour_type})"


class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="tour_images/")

    def __str__(self):
        return f"Фото: {self.tour.title}"


class ItineraryDay(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="itinerary")
    day_number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=128)
    description = models.TextField(validators=[MaxLengthValidator(200)])
    image = models.ImageField(upload_to="itinerary/", null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    altitude = models.CharField(max_length=64, blank=True)
    walking_distance = models.CharField(max_length=64, blank=True)
    driving_distance = models.CharField(max_length=64, blank=True)
    accommodation = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["day_number"]

    def __str__(self):
        return f"{self.tour.title} - День {self.day_number}"


class TourDate(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="dates")
    start_date = models.DateField()
    end_date = models.DateField()
    available_spots = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])

    class Meta:
        ordering = ["start_date"]
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
            )
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
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="price_tiers")
    min_people = models.PositiveSmallIntegerField()
    max_people = models.PositiveSmallIntegerField(null=True, blank=True)
    price_per_person = models.PositiveIntegerField()

    class Meta:
        ordering = ["min_people"]
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
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="extra_services", null=True, blank=True)
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="extra_services/", null=True, blank=True)
    features = models.JSONField(default=list, blank=True)
    price = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    price_label = models.CharField(max_length=64, default="за 1 день тура")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class FAQ(models.Model):
    MAX_FAQ_PER_TOUR = 10

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="faqs", null=True, blank=True)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

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
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="route_points")
    title = models.CharField(max_length=128, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

# ========================
# BOOKING
# ========================

class Booking(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    STATUS_CHOICES = (
        ("pending", "Ожидает подтверждения"),
        ("confirmed", "Подтверждён"),
        ("cancelled", "Отменён"),
        ("rejected", "Отклонён")
    )

    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="bookings")
    tour_date = models.ForeignKey(TourDate, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_start_date = models.DateField(null=True, blank=True)
    preferred_end_date = models.DateField(null=True, blank=True)
    customer_name = models.CharField(max_length=128)
    customer_contact = models.CharField(max_length=128, default="")
    people_details = models.CharField(max_length=255, blank=True, default="")
    comment = models.TextField(blank=True, default="")
    adults = models.PositiveSmallIntegerField(default=1)
    children = models.PositiveSmallIntegerField(default=0)
    number_of_people = models.PositiveSmallIntegerField()
    price_per_person = models.PositiveIntegerField()
    total_price = models.PositiveIntegerField()
    remainder_amount = models.PositiveIntegerField(default=0)
    deposit_percent = models.PositiveSmallIntegerField(default=30)
    deposit_amount = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="booking_status_created_idx"),
            models.Index(fields=["tour", "created_at"], name="booking_tour_created_idx"),
            models.Index(fields=["customer_contact", "created_at"], name="booking_contact_created_idx")
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.tour.title}"

# ========================
# QUIZ
# ========================

class QuizQuestion(models.Model):
    QUESTION_TYPE_CHOICES = (
        ("radio", "Один ответ"),
        ("checkbox", "Несколько ответов"),
        ("text", "Текст")
    )

    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPE_CHOICES, default="radio")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        indexes = [
            models.Index(fields=["is_active", "order"], name="quizq_active_order_idx")
        ]

    def __str__(self):
        return self.text


class QuizAnswerOption(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class QuizLead(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    name = models.CharField(max_length=64, blank=True, default="")
    phone_or_telegram = models.CharField(max_length=64, blank=True, default="")
    answers = models.JSONField()
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Квиз: {self.name} - {self.created_at:%Y-%m-%d}"


class QuizProgress(models.Model):
    session_key = models.CharField(max_length=64, unique=True)
    answers = models.JSONField(default=dict)
    current_question_index = models.PositiveSmallIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(
                fields=["session_key", "is_completed"],
                name="quizprogress_session_done_idx"
            )
        ]

    def __str__(self):
        return f"Прогресс: {self.session_key}"

# ========================
# ATTRACTION
# ========================

class Attraction(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="attractions")
    name = models.CharField(max_length=128)
    description = models.TextField()
    image = models.ImageField(upload_to="attractions/", null=True, blank=True)
    tours = models.ManyToManyField(Tour, blank=True, related_name="attractions")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["city", "is_active"], name="attraction_city_active_idx")
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class AttractionImage(models.Model):
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="attraction_images/")

# ========================
# TRANSFER
# ========================

class TransferRoute(models.Model):
    departure_point = models.CharField(max_length=128)
    arrival_point = models.CharField(max_length=128)
    distance_km = models.PositiveIntegerField()

    class Meta:
        ordering = ["departure_point", "arrival_point"]
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
        ("minibus", "Миниавтобус")
    )

    route = models.ForeignKey(TransferRoute, on_delete=models.CASCADE, related_name="vehicles")
    category = models.CharField(max_length=16, choices=VEHICLE_CATEGORY_CHOICES)
    price = models.PositiveIntegerField()
    seats = models.PositiveSmallIntegerField()
    bags = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["route_id", "category"]
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
        ("rejected", "Отклонён")
    )

    vehicle = models.ForeignKey(VehicleType, on_delete=models.CASCADE)
    travel_date = models.DateField(null=True, blank=True)
    flight_number = models.CharField(max_length=32, blank=True, default="")
    customer_name = models.CharField(max_length=128, blank=True, default="")
    customer_phone = PhoneNumberField()
    passengers = models.PositiveSmallIntegerField(default=1)
    luggage_count = models.PositiveSmallIntegerField(default=0)
    total_price = models.PositiveIntegerField()
    comment = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="transport_status_created_idx"),
            models.Index(fields=["customer_phone", "created_at"], name="transport_phone_created_idx")
        ]

    def __str__(self):
        return f"{self.customer_phone} - {self.vehicle}"

# ========================
# CONTACT
# ========================

class ContactRequest(models.Model):
    DEDUP_WINDOW_MINUTES = 5

    STATUS_CHOICES = (
        ("pending", "Ожидает ответа"),
        ("answered", "Отвечено")
    )

    name = models.CharField(max_length=128)
    phone_or_email = models.CharField(max_length=128)
    message = models.TextField()
    subject = models.CharField(max_length=256, blank=True, default="")
    source = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="contact_status_created_idx"),
            models.Index(fields=["source", "created_at"], name="contact_source_created_idx"),
            models.Index(fields=["phone_or_email", "created_at"], name="contact_email_created_idx")
        ]

    def __str__(self):
        return f"{self.name} - {self.subject or self.source}"