from datetime import date

from django.db.models import Count, Prefetch, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from ..filters import TourFilter
from ..models import (
    Attraction,
    City,
    Country,
    ExtraService,
    FAQ,
    Tour,
    TourCategory,
    TourDate,
    TourPriceTier,
)
from ..serializers import (
    AttractionDetailSerializer,
    AttractionListSerializer,
    CityDetailSerializer,
    CityListSerializer,
    CountryDetailSerializer,
    CountryListSerializer,
    TourCategoryDetailSerializer,
    TourCategoryListSerializer,
    TourDetailSerializer,
    TourListSerializer,
)
from .common import cache_public_api


def active_tour_list_queryset():
    today = date.today()
    dates = Prefetch(
        "dates",
        queryset=TourDate.objects.filter(start_date__gte=today).order_by("start_date"),
        to_attr="prefetched_dates",
    )
    price_tiers = Prefetch(
        "price_tiers",
        queryset=TourPriceTier.objects.order_by("price_per_person"),
    )
    return (
        Tour.objects.filter(is_active=True)
        .select_related("country", "city")
        .prefetch_related("images", "categories", price_tiers, dates)
    )


@cache_public_api
class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Country.objects.prefetch_related(
            "cities",
            Prefetch("tours", queryset=active_tour_list_queryset(), to_attr="active_tours"),
        )

    def get_serializer_class(self):
        return CountryDetailSerializer if self.action == "retrieve" else CountryListSerializer


@cache_public_api
class CityViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return City.objects.select_related("country").prefetch_related(
            Prefetch("tours", queryset=active_tour_list_queryset(), to_attr="active_tours"),
        )

    def get_serializer_class(self):
        return CityDetailSerializer if self.action == "retrieve" else CityListSerializer


@cache_public_api
class TourCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            TourCategory.objects.filter(is_active=True)
            .prefetch_related(Prefetch("tours", queryset=active_tour_list_queryset(), to_attr="active_tours"))
            .annotate(tours_count=Count("tours", filter=Q(tours__is_active=True)))
            .order_by("-tours_count", "order", "id")
        )

    def get_serializer_class(self):
        return TourCategoryDetailSerializer if self.action == "retrieve" else TourCategoryListSerializer


@cache_public_api
class TourViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TourFilter
    search_fields = ["title", "description", "city__city_name"]
    ordering_fields = ["price", "duration_days", "created_at"]

    def get_queryset(self):
        today = date.today()
        price_tiers_p = Prefetch(
            "price_tiers",
            queryset=TourPriceTier.objects.order_by("price_per_person"),
        )
        base = (
            Tour.objects.filter(is_active=True)
            .select_related("country", "city")
            .prefetch_related("images", "categories", price_tiers_p)
        )
        dates_p = Prefetch(
            "dates",
            queryset=TourDate.objects.filter(start_date__gte=today).order_by("start_date"),
            to_attr="prefetched_dates",
        )
        if self.action == "retrieve":
            active_faqs = Prefetch(
                "faqs",
                queryset=FAQ.objects.filter(is_active=True).order_by("order", "id"),
                to_attr="active_faqs",
            )
            active_extra_services = Prefetch(
                "extra_services",
                queryset=ExtraService.objects.filter(is_active=True),
                to_attr="active_extra_services",
            )
            active_attractions = Prefetch(
                "attractions",
                queryset=Attraction.objects.filter(is_active=True).select_related("city"),
                to_attr="active_attractions",
            )
            return base.prefetch_related(
                "itinerary_days",
                "route_points",
                active_faqs,
                active_extra_services,
                active_attractions,
                dates_p,
            )
        return base.prefetch_related(dates_p)

    def get_serializer_class(self):
        return TourDetailSerializer if self.action == "retrieve" else TourListSerializer


@cache_public_api
class AttractionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = (
            Attraction.objects
            .filter(is_active=True)
            .select_related("city", "city__country")
            .prefetch_related(
                "images",
                Prefetch("tours", queryset=active_tour_list_queryset(), to_attr="active_tours"),
            )
            .distinct()
        )

        country = self.request.query_params.get("country")
        city = self.request.query_params.get("city")
        tour = self.request.query_params.get("tour")

        if country:
            country_query = Q(city__country__country_name__iexact=country)
            for lang in ("ru", "en", "es", "fr", "de"):
                country_query |= Q(**{f"city__country__country_name_{lang}__iexact": country})
            if country.isdigit():
                country_query |= Q(city__country_id=int(country))
            queryset = queryset.filter(country_query)

        if city:
            city_query = Q(city__city_name__iexact=city)
            for lang in ("ru", "en", "es", "fr", "de"):
                city_query |= Q(**{f"city__city_name_{lang}__iexact": city})
            if city.isdigit():
                city_query |= Q(city_id=int(city))
            queryset = queryset.filter(city_query)

        if tour and tour.isdigit():
            queryset = queryset.filter(tours__id=int(tour))

        return queryset

    def get_serializer_class(self):
        return AttractionDetailSerializer if self.action == "retrieve" else AttractionListSerializer
