import math
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import get_language
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (FAQ, Attraction, AttractionImage, Booking, City, ContactRequest,
                     Country, ExtraService, ItineraryDay, QuizAnswerOption, QuizLead,
                     QuizProgress, QuizQuestion, SiteSettings, TeamMember, Tour,
                     TourCategory, TourDate, TourImage, TourPriceTier, TourRoutePoint,
                     TransferRoute, TransportRequest, VehicleType)


# ========================
# LANGUAGE HELPERS
# ========================

def is_english():
    language = get_language() or "ru"
    return language.startswith("en")


def get_tour_type_display_value(tour_type):
    if is_english():
        return {
            "group": "Group",
            "private": "Private",
        }.get(tour_type, tour_type)

    return {
        "group": "Групповой",
        "private": "Приватный",
    }.get(tour_type, tour_type)


def get_season_display_value(season):
    if is_english():
        return {
            "all_year": "All year",
            "warm": "Warm season",
            "winter": "Winter",
        }.get(season, season)

    return {
        "all_year": "Круглый год",
        "warm": "Тёплый сезон",
        "winter": "Зима",
    }.get(season, season)


def get_difficulty_display_value(difficulty):
    if is_english():
        return {
            1: "Easy",
            2: "Medium",
            3: "Hard",
        }.get(difficulty, difficulty)

    return {
        1: "Лёгкий",
        2: "Средний",
        3: "Сложный",
    }.get(difficulty, difficulty)


def get_availability_display_value(status):
    if is_english():
        return {
            "available": "Available",
            "almost_full": "Almost full",
            "sold_out": "Sold out",
        }.get(status, status)

    return {
        "available": "Доступно",
        "almost_full": "Почти заполнено",
        "sold_out": "Нет мест",
    }.get(status, status)


def get_vehicle_category_display_value(category):
    if is_english():
        return {
            "sedan": "Sedan",
            "minivan": "Minivan",
            "minibus": "Minibus",
        }.get(category, category)

    return {
        "sedan": "Седан",
        "minivan": "Минивэн",
        "minibus": "Миниавтобус",
    }.get(category, category)


def get_price_display_value(tour):
    if is_english():
        if tour.tour_type == "group":
            return f"from {tour.price} {tour.currency}/person"
        return f"from {tour.price} {tour.currency} per tour"

    if tour.tour_type == "group":
        return f"от {tour.price} {tour.currency}/чел"
    return f"от {tour.price} {tour.currency} за тур"


# ========================
# SITE SETTINGS
# ========================

class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = "__all__"


# ========================
# TEAM
# ========================

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ["id", "full_name", "position", "description", "photo", "order"]


# ========================
# TOUR NESTED SERIALIZERS
# ========================

class TourImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourImage
        fields = ["id", "image"]


class ItineraryDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItineraryDay
        fields = ["id", "day_number", "title", "description", "image",
                  "tags", "altitude", "walking_distance", "driving_distance", "accommodation"]


class TourDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourDate
        fields = ["id", "start_date", "end_date", "available_spots"]


class TourPriceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourPriceTier
        fields = ["id", "min_people", "max_people", "price_per_person"]


class ExtraServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraService
        fields = ["id", "title", "description", "image", "features", "price", "currency", "price_label"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["id", "question", "answer"]


class TourRoutePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourRoutePoint
        fields = ["id", "title", "latitude", "longitude", "order"]


# ========================
# SCHEMA SERIALIZERS
# ========================

class NearestDateSchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    available_spots = serializers.IntegerField()
    price = serializers.IntegerField(required=False)
    currency = serializers.CharField(required=False)


class AvailableDateSchemaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    available_spots = serializers.IntegerField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    price = serializers.IntegerField()
    currency = serializers.CharField()


# ========================
# ATTRACTIONS
# ========================

class AttractionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttractionImage
        fields = ["id", "image"]


class TourShortSerializer(serializers.ModelSerializer):
    cover_image = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    tour_type_display = serializers.SerializerMethodField()
    season_display = serializers.SerializerMethodField()
    difficulty_display = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = ["id", "title", "tour_type", "tour_type_display", "season", "season_display",
                  "duration_days", "difficulty", "difficulty_display", "price", "currency",
                  "price_display", "cover_image", "is_active"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_cover_image(self, tour):
        first_image = tour.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_price_display(self, tour):
        return get_price_display_value(tour)

    @extend_schema_field(serializers.CharField())
    def get_tour_type_display(self, tour):
        return get_tour_type_display_value(tour.tour_type)

    @extend_schema_field(serializers.CharField())
    def get_season_display(self, tour):
        return get_season_display_value(tour.season)

    @extend_schema_field(serializers.CharField())
    def get_difficulty_display(self, tour):
        return get_difficulty_display_value(tour.difficulty)


class AttractionListSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.city_name", read_only=True)
    country_name = serializers.CharField(source="city.country.country_name", read_only=True)

    class Meta:
        model = Attraction
        fields = ["id", "name", "city_name", "country_name", "description", "image"]


class AttractionDetailSerializer(serializers.ModelSerializer):
    city = serializers.SerializerMethodField()
    images = AttractionImageSerializer(many=True, read_only=True)
    nearby_tours = serializers.SerializerMethodField()

    class Meta:
        model = Attraction
        fields = ["id", "name", "city", "description", "image", "images", "nearby_tours", "is_active"]

    @extend_schema_field(serializers.DictField())
    def get_city(self, attraction):
        return {
            "id": attraction.city.id,
            "city_name": attraction.city.city_name,
            "country_name": attraction.city.country.country_name,
        }

    @extend_schema_field(TourShortSerializer(many=True))
    def get_nearby_tours(self, attraction):
        tours = attraction.tours.filter(is_active=True)[:5]
        return TourShortSerializer(tours, many=True).data


# ========================
# COUNTRY
# ========================

class CountryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "country_name", "country_image", "hero_description", "symbol_image"]


class CountryDetailSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()
    tours = serializers.SerializerMethodField()
    attractions = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ["id", "country_name", "country_image", "hero_description", "symbol_image",
                  "cities", "tours", "attractions"]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_cities(self, country):
        return [
            {
                "id": city.id,
                "city_name": city.city_name,
                "city_image": city.city_image.url if city.city_image else None,
            }
            for city in country.cities.all()
        ]

    @extend_schema_field(TourShortSerializer(many=True))
    def get_tours(self, country):
        return TourShortSerializer(country.tours.filter(is_active=True), many=True).data

    @extend_schema_field(AttractionListSerializer(many=True))
    def get_attractions(self, country):
        attractions = Attraction.objects.filter(city__country=country, is_active=True).select_related("city__country")
        return AttractionListSerializer(attractions, many=True).data


# ========================
# CITY
# ========================

class CityListSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.country_name", read_only=True)

    class Meta:
        model = City
        fields = ["id", "city_name", "city_image", "country", "country_name"]


class CityDetailSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.country_name", read_only=True)
    tours = serializers.SerializerMethodField()
    attractions = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ["id", "city_name", "city_image", "country", "country_name", "tours", "attractions"]

    @extend_schema_field(TourShortSerializer(many=True))
    def get_tours(self, city):
        return TourShortSerializer(city.tours.filter(is_active=True), many=True).data

    @extend_schema_field(AttractionListSerializer(many=True))
    def get_attractions(self, city):
        attractions = city.attractions.filter(is_active=True).select_related("city__country")
        return AttractionListSerializer(attractions, many=True).data


# ========================
# CATEGORY
# ========================

class TourCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourCategory
        fields = ["id", "name", "icon"]


class TourCategoryDetailSerializer(serializers.ModelSerializer):
    tours = serializers.SerializerMethodField()

    class Meta:
        model = TourCategory
        fields = ["id", "name", "icon", "tours"]

    @extend_schema_field(TourShortSerializer(many=True))
    def get_tours(self, category):
        return TourShortSerializer(category.tours.filter(is_active=True), many=True).data


# ========================
# TOUR LIST
# ========================

class TourListSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source="country.country_name", read_only=True)
    city_name = serializers.CharField(source="city.city_name", read_only=True)
    cover_image = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    nearest_dates = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    availability_status_display = serializers.SerializerMethodField()
    related_attractions = serializers.SerializerMethodField()
    tour_type_display = serializers.SerializerMethodField()
    season_display = serializers.SerializerMethodField()
    difficulty_display = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = ["id", "title", "tour_type", "tour_type_display", "country_name", "city_name",
                  "season", "season_display", "duration_days", "difficulty", "difficulty_display",
                  "max_people", "price", "currency", "price_display", "cover_image", "nearest_dates",
                  "availability_status", "availability_status_display", "related_attractions",
                  "activity_tags", "is_active", "tripadvisor_url"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_cover_image(self, tour):
        first_image = tour.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_price_display(self, tour):
        return get_price_display_value(tour)

    @extend_schema_field(NearestDateSchemaSerializer(many=True))
    def get_nearest_dates(self, tour):
        if tour.tour_type != "group":
            return []

        today = timezone.now().date()
        upcoming = tour.dates.filter(start_date__gte=today, available_spots__gte=1)[:4]

        return [
            {
                "id": tour_date.id,
                "start_date": tour_date.start_date.isoformat(),
                "end_date": tour_date.end_date.isoformat(),
                "available_spots": tour_date.available_spots,
            }
            for tour_date in upcoming
        ]

    @extend_schema_field(serializers.CharField())
    def get_availability_status(self, tour):
        if tour.tour_type != "group":
            return "available"

        today = timezone.now().date()
        available_dates = tour.dates.filter(start_date__gte=today, available_spots__gte=1)

        if not available_dates.exists():
            return "sold_out"

        nearest_date = available_dates.order_by("start_date").first()
        if (nearest_date.start_date - today).days <= 7:
            return "almost_full"

        return "available"

    @extend_schema_field(serializers.CharField())
    def get_availability_status_display(self, tour):
        return get_availability_display_value(self.get_availability_status(tour))

    @extend_schema_field(AttractionListSerializer(many=True))
    def get_related_attractions(self, tour):
        return AttractionListSerializer(tour.attractions.all()[:3], many=True).data

    @extend_schema_field(serializers.CharField())
    def get_tour_type_display(self, tour):
        return get_tour_type_display_value(tour.tour_type)

    @extend_schema_field(serializers.CharField())
    def get_season_display(self, tour):
        return get_season_display_value(tour.season)

    @extend_schema_field(serializers.CharField())
    def get_difficulty_display(self, tour):
        return get_difficulty_display_value(tour.difficulty)


# ========================
# TOUR DETAIL
# ========================

class TourDetailSerializer(serializers.ModelSerializer):
    country = CountryListSerializer(read_only=True)
    city = CityListSerializer(read_only=True)
    categories = TourCategoryListSerializer(many=True, read_only=True)
    images = TourImageSerializer(many=True, read_only=True)
    itinerary = ItineraryDaySerializer(many=True, read_only=True)
    dates = TourDateSerializer(many=True, read_only=True)
    price_tiers = TourPriceTierSerializer(many=True, read_only=True)
    extra_services = ExtraServiceSerializer(many=True, read_only=True)
    faqs = FAQSerializer(many=True, read_only=True)
    route_points = TourRoutePointSerializer(many=True, read_only=True)
    nearest_date = serializers.SerializerMethodField()
    available_dates = serializers.SerializerMethodField()
    related_attractions = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    tour_type_display = serializers.SerializerMethodField()
    season_display = serializers.SerializerMethodField()
    difficulty_display = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = ["id", "title", "tour_type", "tour_type_display", "country", "city", "categories",
                  "season", "season_display", "duration_days", "difficulty", "difficulty_display",
                  "price", "currency", "price_display", "max_people", "description", "included",
                  "not_included", "images", "itinerary", "dates", "price_tiers", "extra_services",
                  "faqs", "route_points", "nearest_date", "available_dates", "related_attractions",
                  "activity_tags", "tripadvisor_url", "is_active"]

    @extend_schema_field(serializers.CharField())
    def get_price_display(self, tour):
        return get_price_display_value(tour)

    @extend_schema_field(serializers.CharField())
    def get_tour_type_display(self, tour):
        return get_tour_type_display_value(tour.tour_type)

    @extend_schema_field(serializers.CharField())
    def get_season_display(self, tour):
        return get_season_display_value(tour.season)

    @extend_schema_field(serializers.CharField())
    def get_difficulty_display(self, tour):
        return get_difficulty_display_value(tour.difficulty)

    @extend_schema_field(NearestDateSchemaSerializer(allow_null=True))
    def get_nearest_date(self, tour):
        if tour.tour_type != "group":
            return None

        today = timezone.now().date()
        nearest_date = tour.dates.filter(start_date__gte=today, available_spots__gte=1).first()

        if not nearest_date:
            return None

        return {
            "id": nearest_date.id,
            "start_date": nearest_date.start_date.isoformat(),
            "end_date": nearest_date.end_date.isoformat(),
            "available_spots": nearest_date.available_spots,
            "price": tour.price,
            "currency": tour.currency,
        }

    @extend_schema_field(AvailableDateSchemaSerializer(many=True))
    def get_available_dates(self, tour):
        if tour.tour_type != "group":
            return []

        today = timezone.now().date()
        future_dates = tour.dates.filter(start_date__gte=today)

        return [
            {
                "id": tour_date.id,
                "start_date": tour_date.start_date.isoformat(),
                "end_date": tour_date.end_date.isoformat(),
                "available_spots": tour_date.available_spots,
                "status": "available" if tour_date.available_spots > 0 else "sold_out",
                "status_display": get_availability_display_value(
                    "available" if tour_date.available_spots > 0 else "sold_out"
                ),
                "price": tour.price,
                "currency": tour.currency,
            }
            for tour_date in future_dates
        ]

    @extend_schema_field(AttractionListSerializer(many=True))
    def get_related_attractions(self, tour):
        return AttractionListSerializer(tour.attractions.all(), many=True).data


# ========================
# TOUR DATE UPCOMING
# ========================

class TourDateUpcomingSerializer(serializers.ModelSerializer):
    tour_title = serializers.CharField(source="tour.title", read_only=True)
    country_name = serializers.CharField(source="tour.country.country_name", read_only=True)
    tour_duration_days = serializers.IntegerField(source="tour.duration_days", read_only=True)
    tour_price = serializers.IntegerField(source="tour.price", read_only=True)
    tour_currency = serializers.CharField(source="tour.currency", read_only=True)
    tour_cover_image = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    availability_status_display = serializers.SerializerMethodField()
    tour_type = serializers.CharField(source="tour.tour_type", read_only=True)
    tour_type_display = serializers.SerializerMethodField()
    season = serializers.CharField(source="tour.season", read_only=True)
    season_display = serializers.SerializerMethodField()

    class Meta:
        model = TourDate
        fields = ["id", "tour", "tour_title", "country_name", "tour_cover_image",
                  "tour_duration_days", "tour_type", "tour_type_display", "season", "season_display",
                  "start_date", "end_date", "available_spots", "availability_status",
                  "availability_status_display", "tour_price", "tour_currency"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_tour_cover_image(self, tour_date):
        first_image = tour_date.tour.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        return None

    @extend_schema_field(serializers.CharField())
    def get_availability_status(self, tour_date):
        return "available" if tour_date.available_spots > 0 else "sold_out"

    @extend_schema_field(serializers.CharField())
    def get_availability_status_display(self, tour_date):
        return get_availability_display_value(self.get_availability_status(tour_date))

    @extend_schema_field(serializers.CharField())
    def get_tour_type_display(self, tour_date):
        return get_tour_type_display_value(tour_date.tour.tour_type)

    @extend_schema_field(serializers.CharField())
    def get_season_display(self, tour_date):
        return get_season_display_value(tour_date.tour.season)


# ========================
# BOOKING
# ========================

class BookingCreateSerializer(serializers.ModelSerializer):
    PRIVATE_MAX_PEOPLE = 999

    total_price = serializers.IntegerField(read_only=True)
    price_per_person = serializers.IntegerField(read_only=True)
    remainder_amount = serializers.IntegerField(read_only=True)
    deposit_amount = serializers.IntegerField(read_only=True)
    deposit_percent = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    number_of_people = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "tour", "tour_date", "preferred_start_date", "preferred_end_date",
                  "customer_name", "customer_contact", "people_details", "comment",
                  "adults", "children", "number_of_people", "price_per_person",
                  "total_price", "remainder_amount", "deposit_percent", "deposit_amount", "status"]

    def _find_duplicate(self, tour, customer_contact):
        window = timezone.now() - timedelta(minutes=Booking.DEDUP_WINDOW_MINUTES)
        return Booking.objects.filter(tour=tour, customer_contact=customer_contact, created_at__gte=window).first()

    def validate(self, attrs):
        tour = attrs["tour"]
        tour_date = attrs.get("tour_date")
        preferred_start_date = attrs.get("preferred_start_date")
        adults = attrs.get("adults", 0)
        children = attrs.get("children", 0)
        total_people = adults + children

        if not tour.is_active:
            raise serializers.ValidationError({"tour": "Нельзя забронировать неактивный тур."})

        if total_people < 1:
            raise serializers.ValidationError({"adults": "Нужно указать хотя бы одного человека."})

        if tour.tour_type == "group":
            if not tour_date:
                raise serializers.ValidationError({"tour_date": "Для группового тура нужно выбрать дату."})

            if preferred_start_date:
                raise serializers.ValidationError({"preferred_start_date": "Для группового тура нельзя указывать гибкую дату."})

            if tour_date.tour_id != tour.id:
                raise serializers.ValidationError({"tour_date": "Эта дата не принадлежит выбранному туру."})

            if tour_date.start_date < date.today():
                raise serializers.ValidationError({"tour_date": "Нельзя забронировать прошедшую дату."})

            if total_people > tour_date.available_spots:
                raise serializers.ValidationError({"adults": f"Недостаточно мест. Осталось: {tour_date.available_spots}."})

            if tour.max_people and total_people > tour.max_people:
                raise serializers.ValidationError({"adults": f"Максимум {tour.max_people} человек."})

        elif tour.tour_type == "private":
            if tour_date:
                raise serializers.ValidationError({"tour_date": "Для приватного тура нельзя выбирать фиксированную дату."})

            if not preferred_start_date:
                raise serializers.ValidationError({"preferred_start_date": "Для приватного тура нужно указать дату начала."})

            if preferred_start_date < date.today():
                raise serializers.ValidationError({"preferred_start_date": "Нельзя выбрать дату в прошлом."})

            preferred_end_date = attrs.get("preferred_end_date")

            if preferred_end_date and preferred_end_date < preferred_start_date:
                raise serializers.ValidationError({"preferred_end_date": "Дата окончания не может быть раньше даты начала."})

            if total_people > self.PRIVATE_MAX_PEOPLE:
                raise serializers.ValidationError({"adults": f"Максимум {self.PRIVATE_MAX_PEOPLE} человек."})

        attrs["number_of_people"] = total_people
        return attrs

    def _find_price_tier(self, tour, number_of_people):
        return (
            tour.price_tiers
            .filter(min_people__lte=number_of_people)
            .filter(Q(max_people__gte=number_of_people) | Q(max_people__isnull=True))
            .order_by("-min_people")
            .first()
        )

    @transaction.atomic
    def create(self, validated_data):
        tour = validated_data["tour"]
        number_of_people = validated_data["number_of_people"]
        customer_contact = validated_data["customer_contact"]

        duplicate = self._find_duplicate(tour, customer_contact)

        if duplicate:
            self.is_duplicate = True
            return duplicate

        self.is_duplicate = False

        if tour.tour_type == "group":
            locked_date = TourDate.objects.select_for_update().get(pk=validated_data["tour_date"].pk, tour=tour)

            if number_of_people > locked_date.available_spots:
                raise serializers.ValidationError({"adults": f"Недостаточно мест. Осталось: {locked_date.available_spots}."})

            price_per_person = tour.price
            total_price = tour.price * number_of_people
            remainder_amount = 0

            locked_date.available_spots -= number_of_people
            locked_date.save(update_fields=["available_spots"])

            saved_tour_date = locked_date
            saved_start_date = None
            saved_end_date = None

        else:
            tier = self._find_price_tier(tour, number_of_people)

            if tier:
                price_per_person = tier.price_per_person
                total_price = tier.price_per_person * number_of_people
                remainder_amount = 0
            else:
                total_price = tour.price
                price_per_person = tour.price // number_of_people
                remainder_amount = tour.price % number_of_people

            saved_tour_date = None
            saved_start_date = validated_data.get("preferred_start_date")
            saved_end_date = validated_data.get("preferred_end_date")

        deposit_amount = math.ceil(total_price * 30 / 100)

        return Booking.objects.create(
            tour=tour,
            tour_date=saved_tour_date,
            preferred_start_date=saved_start_date,
            preferred_end_date=saved_end_date,
            customer_name=validated_data["customer_name"],
            customer_contact=customer_contact,
            people_details=validated_data.get("people_details", ""),
            comment=validated_data.get("comment", ""),
            adults=validated_data.get("adults", 0),
            children=validated_data.get("children", 0),
            number_of_people=number_of_people,
            price_per_person=price_per_person,
            total_price=total_price,
            remainder_amount=remainder_amount,
            deposit_percent=30,
            deposit_amount=deposit_amount,
            status="pending",
        )


class BookingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "status"]


# ========================
# QUIZ
# ========================

class QuizAnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswerOption
        fields = ["id", "text", "order"]


class QuizQuestionSerializer(serializers.ModelSerializer):
    options = QuizAnswerOptionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ["id", "text", "question_type", "order", "options"]


class QuizLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizLead
        fields = ["id", "name", "phone_or_telegram", "answers", "is_processed", "created_at"]
        read_only_fields = ["id", "is_processed", "created_at"]

    def validate_answers(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("answers должен быть JSON-объектом (dict).")
        return value

    def _find_duplicate(self, phone_or_telegram):
        if not phone_or_telegram:
            return None

        window = timezone.now() - timedelta(minutes=QuizLead.DEDUP_WINDOW_MINUTES)
        return QuizLead.objects.filter(phone_or_telegram=phone_or_telegram, created_at__gte=window).first()

    def create(self, validated_data):
        phone_or_telegram = validated_data.get("phone_or_telegram", "")

        duplicate = self._find_duplicate(phone_or_telegram)

        if duplicate:
            self.is_duplicate = True
            return duplicate

        self.is_duplicate = False
        return QuizLead.objects.create(**validated_data)


class QuizProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizProgress
        fields = ["id", "answers", "current_question_index", "is_completed", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class QuizProgressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizProgress
        fields = ["answers", "current_question_index"]


# ========================
# TRANSFER
# ========================

class VehicleTypeSerializer(serializers.ModelSerializer):
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = VehicleType
        fields = ["id", "category", "category_display", "price", "seats", "bags"]

    @extend_schema_field(serializers.CharField())
    def get_category_display(self, vehicle):
        return get_vehicle_category_display_value(vehicle.category)


class TransferRouteSerializer(serializers.ModelSerializer):
    vehicles = VehicleTypeSerializer(many=True, read_only=True)

    class Meta:
        model = TransferRoute
        fields = ["id", "departure_point", "arrival_point", "distance_km", "vehicles"]


class TransportRequestCreateSerializer(serializers.ModelSerializer):
    total_price = serializers.IntegerField(read_only=True)

    class Meta:
        model = TransportRequest
        fields = ["id", "vehicle", "customer_phone", "passengers", "travel_date",
                  "flight_number", "customer_name", "luggage_count", "comment", "total_price"]

    def _find_duplicate(self, vehicle, customer_phone):
        window = timezone.now() - timedelta(minutes=TransportRequest.DEDUP_WINDOW_MINUTES)
        return TransportRequest.objects.filter(vehicle=vehicle, customer_phone=customer_phone, created_at__gte=window).first()

    def validate(self, attrs):
        vehicle = attrs["vehicle"]
        passengers = attrs.get("passengers", 1)
        luggage_count = attrs.get("luggage_count", 0)
        travel_date = attrs.get("travel_date")

        if travel_date and travel_date < date.today():
            raise serializers.ValidationError({"travel_date": "Нельзя выбрать дату в прошлом."})

        if passengers < 1:
            raise serializers.ValidationError({"passengers": "Минимум 1 пассажир."})

        if passengers > vehicle.seats:
            raise serializers.ValidationError(
                {"passengers": f"В {get_vehicle_category_display_value(vehicle.category)} максимум {vehicle.seats} мест."}
            )

        if luggage_count > vehicle.bags:
            raise serializers.ValidationError(
                {"luggage_count": f"В {get_vehicle_category_display_value(vehicle.category)} максимум {vehicle.bags} мест для багажа."}
            )

        return attrs

    def create(self, validated_data):
        vehicle = validated_data["vehicle"]
        customer_phone = validated_data["customer_phone"]

        duplicate = self._find_duplicate(vehicle, customer_phone)

        if duplicate:
            self.is_duplicate = True
            return duplicate

        self.is_duplicate = False

        return TransportRequest.objects.create(total_price=vehicle.price, status="pending", **validated_data)


class TransportRequestStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportRequest
        fields = ["id", "status"]


# ========================
# CONTACT
# ========================

class ContactRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = ["id", "subject", "name", "phone_or_email", "message", "source", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def _find_duplicate(self, phone_or_email, message):
        window = timezone.now() - timedelta(minutes=ContactRequest.DEDUP_WINDOW_MINUTES)
        return ContactRequest.objects.filter(phone_or_email=phone_or_email, message=message, created_at__gte=window).first()

    def create(self, validated_data):
        phone_or_email = validated_data["phone_or_email"]
        message = validated_data["message"]

        duplicate = self._find_duplicate(phone_or_email, message)

        if duplicate:
            self.is_duplicate = True
            return duplicate

        self.is_duplicate = False
        return ContactRequest.objects.create(**validated_data)
