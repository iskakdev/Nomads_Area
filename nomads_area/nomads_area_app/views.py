from datetime import date
from django.db import transaction
from django.conf import settings
from django.db.models import Count, Prefetch, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .filters import TourFilter
from .models import (Attraction, City, Country, ExtraService, FAQ, QuizProgress,
                     QuizQuestion, SiteSettings, TeamMember, Tour, TourCategory,
                     TourDate, TourPriceTier)
from .notifications import (send_booking_notification, send_contact_notification,
                            send_quiz_notification)
from .serializers import (AttractionDetailSerializer, AttractionListSerializer, BookingCreateSerializer,
                          CityDetailSerializer, CityListSerializer, ContactRequestSerializer,
                          CountryDetailSerializer, CountryListSerializer, QuizLeadSerializer,
                          QuizProgressSerializer, QuizProgressUpdateSerializer, QuizQuestionSerializer,
                          SiteSettingsSerializer, TeamMemberSerializer, TourCategoryDetailSerializer,
                          TourCategoryListSerializer, TourDetailSerializer, TourListSerializer,
                          )
from .services import update_quiz_progress_service
from .throttles import FormSubmitThrottle

cache_public_api = method_decorator(
    cache_page(
        settings.API_CACHE_TIMEOUT,
        key_prefix=settings.API_CACHE_KEY_PREFIX,
    ),
    name="dispatch",
)


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
class SiteSettingsView(generics.RetrieveAPIView):
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return SiteSettings.get_settings()


@cache_public_api
class TeamMemberListView(generics.ListAPIView):
    queryset = TeamMember.objects.filter(is_active=True)
    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]


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


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        booking = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_booking_notification(booking))


@cache_public_api
class QuizQuestionListView(generics.ListAPIView):
    queryset = QuizQuestion.objects.filter(is_active=True).prefetch_related("options")
    serializer_class = QuizQuestionSerializer
    permission_classes = [AllowAny]


class QuizProgressStartView(generics.CreateAPIView):
    serializer_class = QuizProgressSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        if not request.session.session_key:
            request.session.save()
        progress, created = QuizProgress.objects.get_or_create(
            session_key=request.session.session_key,
            defaults={"answers_data": {}, "current_question_index": 0},
        )
        if not created and progress.is_completed:
            progress.answers_data = {}
            progress.current_question_index = 0
            progress.is_completed = False
            progress.save(update_fields=["answers_data", "current_question_index", "is_completed"])
        return Response(self.get_serializer(progress).data, status=status.HTTP_200_OK)


class QuizProgressUpdateView(generics.UpdateAPIView):
    serializer_class = QuizProgressUpdateSerializer
    permission_classes = [AllowAny]
    lookup_field = "session_key"

    def get_object(self):
        key = self.kwargs.get(self.lookup_field) or self.request.session.session_key
        return generics.get_object_or_404(QuizProgress, session_key=key)

    def update(self, request, *args, **kwargs):
        progress = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        progress = update_quiz_progress_service(progress, serializer.validated_data)
        return Response(QuizProgressSerializer(progress).data, status=status.HTTP_200_OK)


class QuizLeadCreateView(generics.CreateAPIView):
    serializer_class = QuizLeadSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        lead = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_quiz_notification(lead))


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


class ContactRequestCreateView(generics.CreateAPIView):
    serializer_class = ContactRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        instance = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_contact_notification(instance))
