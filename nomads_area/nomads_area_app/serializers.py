from datetime import date
from django.utils.translation import get_language
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import (Attraction, AttractionImage, Booking, City, ContactRequest, Country,
                     ExtraService, FAQ, ItineraryDay, QuizLead, QuizProgress,
                     QuizQuestion, SiteSettings, TeamMember, Tour, TourCategory, TourDate,
                     TourImage, TourPriceTier, TourRoutePoint)
from .services import (create_booking_service, create_contact_request_service,
                       create_quiz_lead_service)


def is_english():
    return (get_language() or "ru").startswith("en")

def get_request_language(context=None):
    request = (context or {}).get("request")
    if request:
        parts = request.path_info.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            return parts[1].split("-")[0]

    return (get_language() or "ru").split("-")[0]


def localized_value(obj, field, lang="ru", default_lang="ru"):
    for code in [lang, "en", default_lang]:
        value = getattr(obj, f"{field}_{code}", None)
        if value:
            return value

    return getattr(obj, field, "")


class LocalizedModelSerializer(serializers.ModelSerializer):
    localized_fields = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = get_request_language(self.context)

        for field in self.localized_fields:
            if field in data:
                data[field] = localized_value(instance, field, lang)

        return data

def _file_url(instance, field, request=None):
    f = getattr(instance, field, None)
    return request.build_absolute_uri(f.url) if f and request else f.url if f else None

def _disp(val, en_map, ru_map):
    return en_map.get(val, val) if is_english() else ru_map.get(val, val)

def get_tour_type_display(v):
    return _disp(v, {"group": "Group", "private": "Private"}, {"group": "Групповой", "private": "Приватный"})

def get_season_display(v):
    return _disp(v, {"all_year": "All year", "warm": "Warm", "winter": "Winter"}, {"all_year": "Круглый год", "warm": "Тёплый", "winter": "Зима"})

class SiteSettingsSerializer(LocalizedModelSerializer):
    localized_fields = ("about_text", "privacy_policy")
    class Meta:
        model = SiteSettings
        fields = ["id", "phone", "whatsapp", "email",
                  "instagram_url", "facebook_url", "youtube_url", "tiktok_url", "tripadvisor_url",
                  "about_text", "about_video_url",
                  "years_experience", "tourists_count", "routes_count",
                  "reviews_enabled", "elfsight_google_reviews_app_id", "privacy_policy"]


class TeamMemberSerializer(LocalizedModelSerializer):
    localized_fields = ("full_name", "position", "description")
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = ["id", "full_name", "position", "description", "photo", "photo_url"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_photo_url(self, obj):
        return _file_url(obj, "photo", self.context.get("request"))


class CountryListSerializer(LocalizedModelSerializer):
    localized_fields = ("country_name",)
    country_image_url = serializers.SerializerMethodField()
    symbol_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ["id", "country_name", "country_image", "country_image_url", "symbol_image", "symbol_image_url"]

    def get_country_image_url(self, obj): return _file_url(obj, "country_image", self.context.get("request"))
    def get_symbol_image_url(self, obj): return _file_url(obj, "symbol_image", self.context.get("request"))


class CityListSerializer(LocalizedModelSerializer):
    localized_fields = ("city_name", "description")
    city_image_url = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ["id", "city_name", "city_image", "city_image_url", "description"]

    def get_city_image_url(self, obj): return _file_url(obj, "city_image", self.context.get("request"))


class TourCategoryListSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TourCategory
        fields = ["id", "name", "image", "image_url", "description"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


class TourCategoryShortSerializer(LocalizedModelSerializer):
    localized_fields = ("name",)
    """Короткий сериализатор категории — только для вложения в тур."""
    class Meta:
        model = TourCategory
        fields = ["id", "name"]


class TourDateUpcomingSerializer(LocalizedModelSerializer):
    class Meta:
        model = TourDate
        fields = ["id", "start_date", "end_date", "available_spots"]


class TourPriceTierSerializer(LocalizedModelSerializer):
    class Meta:
        model = TourPriceTier
        fields = ["id", "min_people", "max_people", "price_per_person"]


class TourImageSerializer(LocalizedModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TourImage
        fields = ["id", "image", "image_url", "alt_text", "order"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


def get_display_price(obj):
    if obj.tour_type == Tour.TOUR_TYPE_PRIVATE:
        tiers = obj.price_tiers.all()
        tier = min(tiers, key=lambda item: item.price_per_person, default=None)
        return tier.price_per_person if tier else obj.price
    return obj.price


class TourListSerializer(LocalizedModelSerializer):
    localized_fields = ("title",)
    price = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    tour_type_display = serializers.SerializerMethodField()
    season_display = serializers.SerializerMethodField()
    upcoming_dates = serializers.SerializerMethodField()
    categories = TourCategoryShortSerializer(many=True, read_only=True)

    class Meta:
        model = Tour
        fields = ["id", "title", "tour_type", "tour_type_display", "season", "season_display",
                  "duration_days", "difficulty", "price", "currency", "max_group_size",
                  "cover_image", "upcoming_dates", "categories"]

    def get_cover_image(self, obj):
        imgs = obj.images.all()
        return _file_url(imgs[0], "image", self.context.get("request")) if imgs else None

    def get_price(self, obj):
        return get_display_price(obj)

    def get_tour_type_display(self, obj): return get_tour_type_display(obj.tour_type)
    def get_season_display(self, obj): return get_season_display(obj.season)

    def get_upcoming_dates(self, obj):
        dates = getattr(obj, "prefetched_dates", None)
        if dates is None:
            dates = obj.dates.filter(start_date__gte=date.today()).order_by("start_date")[:3]
        return TourDateUpcomingSerializer(dates[:3], many=True).data


class FAQSerializer(LocalizedModelSerializer):
    localized_fields = ("question", "answer")
    class Meta:
        model = FAQ
        fields = ["question", "answer"]


class TourRoutePointSerializer(LocalizedModelSerializer):
    class Meta:
        model = TourRoutePoint
        fields = ["title", "latitude", "longitude"]


class ExtraServiceSerializer(LocalizedModelSerializer):
    localized_fields = ("title", "description", "features", "price_label")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ExtraService
        fields = ["id", "title", "description", "image", "image_url", "features", "price", "currency", "price_label"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


class ItineraryDaySerializer(LocalizedModelSerializer):
    localized_fields = ("title", "description", "altitude", "walking_distance", "driving_distance", "accommodation")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ItineraryDay
        fields = ["day_number", "title", "description", "image", "image_url", "altitude", "walking_distance", "driving_distance", "accommodation"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


class AttractionInTourSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    """
    Лёгкая версия достопримечательности для вложения в тур.
    Не содержит список туров - иначе была бы бесконечная рекурсия:
    тур -> достопримечательность -> тур -> достопримечательность -> ...
    """
    image_url = serializers.SerializerMethodField()
    city_name = serializers.CharField(source="city.city_name", read_only=True)

    class Meta:
        model = Attraction
        fields = ["id", "name", "description", "image", "image_url", "city_name"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


class TourDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("title", "description", "included", "not_included")
    price = serializers.SerializerMethodField()
    images = TourImageSerializer(many=True, read_only=True)
    itinerary_days = ItineraryDaySerializer(many=True, read_only=True)
    faqs = FAQSerializer(many=True, read_only=True)
    extra_services = ExtraServiceSerializer(many=True, read_only=True)
    route_points = TourRoutePointSerializer(many=True, read_only=True)
    price_tiers = TourPriceTierSerializer(many=True, read_only=True)
    attractions = AttractionInTourSerializer(many=True, read_only=True)
    categories = TourCategoryShortSerializer(many=True, read_only=True)
    tour_type_display = serializers.SerializerMethodField()
    season_display = serializers.SerializerMethodField()
    upcoming_dates = serializers.SerializerMethodField()

    class Meta:
        model = Tour
        fields = ["id", "title", "description", "tour_type", "tour_type_display",
                  "season", "season_display", "duration_days", "difficulty",
                  "price", "currency", "max_group_size", "included", "not_included",
                  "categories", "images", "itinerary_days", "faqs", "extra_services",
                  "route_points", "price_tiers", "attractions", "upcoming_dates"]

    def get_tour_type_display(self, obj): return get_tour_type_display(obj.tour_type)
    def get_season_display(self, obj): return get_season_display(obj.season)

    def get_price(self, obj):
        return get_display_price(obj)

    def get_upcoming_dates(self, obj):
        dates = getattr(obj, "prefetched_dates", None)
        if dates is None:
            dates = obj.dates.filter(start_date__gte=date.today()).order_by("start_date")
        return TourDateUpcomingSerializer(dates, many=True).data


class TourCategoryDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    image_url = serializers.SerializerMethodField()
    tours = serializers.SerializerMethodField()

    class Meta:
        model = TourCategory
        fields = ["id", "name", "image", "image_url", "description", "tours"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))
    def get_tours(self, obj): return TourListSerializer(obj.tours.filter(is_active=True), many=True, context=self.context).data


class CountryDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("country_name", "hero_description")
    country_image_url = serializers.SerializerMethodField()
    symbol_image_url = serializers.SerializerMethodField()
    cities = CityListSerializer(many=True, read_only=True)
    tours = serializers.SerializerMethodField()

    class Meta:
        model = Country
        fields = ["id", "country_name", "country_image", "country_image_url", "hero_description",
                  "symbol_image", "symbol_image_url", "cities", "tours"]

    def get_country_image_url(self, obj): return _file_url(obj, "country_image", self.context.get("request"))
    def get_symbol_image_url(self, obj): return _file_url(obj, "symbol_image", self.context.get("request"))
    def get_tours(self, obj): return TourListSerializer(obj.tours.filter(is_active=True), many=True, context=self.context).data


class CityDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("city_name", "description")
    city_image_url = serializers.SerializerMethodField()
    tours = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ["id", "city_name", "city_image", "city_image_url", "description", "tours"]

    def get_city_image_url(self, obj): return _file_url(obj, "city_image", self.context.get("request"))
    def get_tours(self, obj): return TourListSerializer(obj.tours.filter(is_active=True), many=True, context=self.context).data


class BookingCreateSerializer(LocalizedModelSerializer):
    number_of_people = serializers.SerializerMethodField()
    price_per_person = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    extra_services = serializers.PrimaryKeyRelatedField(queryset=ExtraService.objects.filter(is_active=True), many=True, required=False)

    class Meta:
        model = Booking
        fields = ["id", "tour", "tour_date", "preferred_start_date", "preferred_end_date",
                  "customer_name", "customer_contact", "adults", "children", "comment",
                  "extra_services", "number_of_people", "price_per_person", "total_price",
                  "currency", "status", "created_at"]
        read_only_fields = ["id", "number_of_people", "price_per_person", "total_price",
                            "currency", "status", "created_at"]

    def validate(self, attrs):
        tour = attrs["tour"]
        tour_date = attrs.get("tour_date")
        total = attrs["adults"] + attrs.get("children", 0)
        self._price_tier = self._resolved_date = None

        if total <= 0:
            raise serializers.ValidationError({"non_field_errors": "Количество людей > 0"})

        if tour.tour_type == Tour.TOUR_TYPE_GROUP:
            if not tour_date:
                raise serializers.ValidationError({"tour_date": "Выберите дату"})
            if tour_date.tour_id != tour.id:
                raise serializers.ValidationError({"tour_date": "Не та дата"})
            if tour_date.start_date < date.today():
                raise serializers.ValidationError({"tour_date": "Дата в прошлом"})
            if total > tour_date.available_spots:
                raise serializers.ValidationError({"non_field_errors": f"Мест: {tour_date.available_spots}"})
            self._resolved_date = tour_date

        elif tour.tour_type == Tour.TOUR_TYPE_PRIVATE:
            if tour_date:
                raise serializers.ValidationError({"tour_date": "Приватный без фикс. даты"})
            s, e = attrs.get("preferred_start_date"), attrs.get("preferred_end_date")
            if not s or not e:
                raise serializers.ValidationError({"preferred_start_date": "Укажите диапазон"})
            if s < date.today() or s > e:
                raise serializers.ValidationError({"preferred_end_date": "Некорректные даты"})
            tier = tour.price_tiers.filter(min_people__lte=total, max_people__gte=total).first() or \
                   tour.price_tiers.filter(min_people__lte=total, max_people__isnull=True).first()
            if not tier:
                raise serializers.ValidationError({"non_field_errors": f"Нет тарифа для {total} чел"})
            self._price_tier = tier

        extra_services = attrs.get("extra_services") or []
        invalid_services = [service.id for service in extra_services if service.tour_id != tour.id]
        if invalid_services:
            raise serializers.ValidationError({"extra_services": "Услуга не относится к выбранному туру"})

        return attrs

    def create(self, validated_data):
        b, is_dup = create_booking_service(
            validated_data,
            price_tier=self._price_tier,
            tour_date=self._resolved_date,
        )
        self.is_duplicate = is_dup
        return b

    def get_number_of_people(self, obj): return obj.number_of_people
    def get_price_per_person(self, obj): return obj.price_per_person
    def get_total_price(self, obj): return obj.total_price


class QuizQuestionSerializer(LocalizedModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = ["id", "question_text", "question_type", "options"]

    def get_options(self, obj):
        return [{"id": o.id, "option_text": o.option_text, "next_question": o.next_question_id} for o in obj.options.all()]


class QuizProgressSerializer(LocalizedModelSerializer):
    class Meta:
        model = QuizProgress
        fields = ["session_key", "answers_data", "current_question_index", "is_completed", "updated_at"]
        read_only_fields = fields


class QuizProgressUpdateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_options = serializers.ListField(child=serializers.IntegerField(), required=False)
    text_answer = serializers.CharField(required=False, allow_blank=True)


class QuizLeadSerializer(LocalizedModelSerializer):
    answers = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = QuizLead
        fields = ["id", "customer_name", "customer_contact", "answers", "answers_data", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def create(self, validated_data):
        answers = validated_data.pop("answers", None)
        if answers is not None and not validated_data.get("answers_data"):
            validated_data["answers_data"] = answers

        i, is_dup = create_quiz_lead_service(validated_data)
        self.is_duplicate = is_dup
        return i


class ContactRequestSerializer(LocalizedModelSerializer):
    class Meta:
        model = ContactRequest
        fields = ["id", "subject", "name", "phone_or_email", "message", "source", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def create(self, validated_data):
        i, is_dup = create_contact_request_service(validated_data)
        self.is_duplicate = is_dup
        return i


class AttractionImageSerializer(LocalizedModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AttractionImage
        fields = ["id", "image", "image_url", "alt_text", "order"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


class AttractionListSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Attraction
        fields = ["id", "name", "description", "image", "image_url"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))


class AttractionDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    image_url = serializers.SerializerMethodField()
    images = AttractionImageSerializer(many=True, read_only=True)
    tours = TourListSerializer(many=True, read_only=True)

    class Meta:
        model = Attraction
        fields = ["id", "name", "description", "image", "image_url", "images", "tours"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))
