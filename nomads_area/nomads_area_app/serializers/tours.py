from datetime import date

from rest_framework import serializers

from ..models import (
    Attraction,
    AttractionImage,
    City,
    Country,
    ItineraryDay,
    Tour,
    TourCategory,
    TourDate,
    TourImage,
    TourPriceTier,
    TourRoutePoint,
)
from .common import (
    LocalizedModelSerializer,
    _file_url,
    get_request_language,
    get_season_display,
    get_tour_type_display,
    localized_value,
)
from .content import FAQSerializer, ExtraServiceSerializer


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
    localized_fields = ("city_name",)

    class Meta:
        model = City
        fields = ["id", "city_name"]

class TourCategoryListSerializer(LocalizedModelSerializer):
    localized_fields = ("name",)

    class Meta:
        model = TourCategory
        fields = ["id", "name"]

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

class TourRoutePointSerializer(LocalizedModelSerializer):
    class Meta:
        model = TourRoutePoint
        fields = ["title", "latitude", "longitude"]

class ItineraryDaySerializer(LocalizedModelSerializer):
    localized_fields = ("title", "description", "altitude", "walking_distance", "driving_distance", "accommodation")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ItineraryDay
        fields = ["day_number", "title", "description", "image", "image_url", "altitude", "walking_distance", "driving_distance", "accommodation", "tags"]

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
    faqs = serializers.SerializerMethodField()
    extra_services = serializers.SerializerMethodField()
    route_points = TourRoutePointSerializer(many=True, read_only=True)
    price_tiers = TourPriceTierSerializer(many=True, read_only=True)
    attractions = serializers.SerializerMethodField()
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

    def get_faqs(self, obj):
        faqs = getattr(obj, "active_faqs", None)
        if faqs is None:
            faqs = obj.faqs.filter(is_active=True)
        return FAQSerializer(faqs, many=True, context=self.context).data

    def get_extra_services(self, obj):
        services = getattr(obj, "active_extra_services", None)
        if services is None:
            services = obj.extra_services.filter(is_active=True)
        return ExtraServiceSerializer(services, many=True, context=self.context).data

    def get_attractions(self, obj):
        attractions = getattr(obj, "active_attractions", None)
        if attractions is None:
            attractions = obj.attractions.filter(is_active=True)
        return AttractionInTourSerializer(attractions, many=True, context=self.context).data

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
    def get_tours(self, obj):
        tours = getattr(obj, "active_tours", None)
        if tours is None:
            tours = obj.tours.filter(is_active=True)
        return TourListSerializer(tours, many=True, context=self.context).data

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
    def get_tours(self, obj):
        tours = getattr(obj, "active_tours", None)
        if tours is None:
            tours = obj.tours.filter(is_active=True)
        return TourListSerializer(tours, many=True, context=self.context).data

class CityDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("city_name",)
    tours = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ["id", "city_name", "tours"]

    def get_tours(self, obj):
        tours = getattr(obj, "active_tours", None)
        if tours is None:
            tours = obj.tours.filter(is_active=True)
        return TourListSerializer(tours, many=True, context=self.context).data

class AttractionImageSerializer(LocalizedModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AttractionImage
        fields = ["id", "image", "image_url", "alt_text", "order"]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))

class AttractionListSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    image_url = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    country_id = serializers.IntegerField(source="city.country_id", read_only=True)
    country_name = serializers.SerializerMethodField()

    class Meta:
        model = Attraction
        fields = [
            "id", "name", "description", "image", "image_url",
            "city", "city_name", "country_id", "country_name",
        ]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))
    def get_city_name(self, obj): return localized_value(obj.city, "city_name", get_request_language(self.context))
    def get_country_name(self, obj): return localized_value(obj.city.country, "country_name", get_request_language(self.context))

class AttractionDetailSerializer(LocalizedModelSerializer):
    localized_fields = ("name", "description")
    image_url = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    country_id = serializers.IntegerField(source="city.country_id", read_only=True)
    country_name = serializers.SerializerMethodField()
    images = AttractionImageSerializer(many=True, read_only=True)
    tours = serializers.SerializerMethodField()

    class Meta:
        model = Attraction
        fields = [
            "id", "name", "description", "image", "image_url",
            "city", "city_name", "country_id", "country_name", "images", "tours",
        ]

    def get_image_url(self, obj): return _file_url(obj, "image", self.context.get("request"))
    def get_city_name(self, obj): return localized_value(obj.city, "city_name", get_request_language(self.context))
    def get_country_name(self, obj): return localized_value(obj.city.country, "country_name", get_request_language(self.context))
    def get_tours(self, obj):
        tours = getattr(obj, "active_tours", None)
        if tours is None:
            tours = obj.tours.filter(is_active=True)
        return TourListSerializer(tours, many=True, context=self.context).data
