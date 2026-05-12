import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .filters import TourFilter
from .models import (Attraction, City, Country, QuizProgress, QuizQuestion,
                     SiteSettings, TeamMember, Tour, TourCategory, TourDate,
                     TransferRoute, TransportRequest)
from .notifications import (send_booking_notification, send_contact_notification,
                             send_quiz_notification, send_transport_notification)
from .serializers import (AttractionDetailSerializer, AttractionListSerializer,
                          BookingCreateSerializer, CityDetailSerializer, CityListSerializer,
                          ContactRequestSerializer, CountryDetailSerializer, CountryListSerializer,
                          QuizLeadSerializer, QuizProgressSerializer, QuizProgressUpdateSerializer,
                          QuizQuestionSerializer, SiteSettingsSerializer, TeamMemberSerializer,
                          TourCategoryDetailSerializer, TourCategoryListSerializer,
                          TourDateUpcomingSerializer, TourDetailSerializer, TourListSerializer,
                          TransferRouteSerializer, TransportRequestCreateSerializer)
from .throttles import FormSubmitThrottle


logger = logging.getLogger(__name__)


# ========================
# SITE SETTINGS
# ========================

class SiteSettingsView(generics.RetrieveAPIView):
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return SiteSettings.get_settings()


class TeamMemberListView(generics.ListAPIView):
    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]
    queryset = TeamMember.objects.filter(is_active=True).order_by("order", "id")


# ========================
# СПРАВОЧНИКИ
# ========================

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.action == "retrieve":
            return (
                Country.objects
                .prefetch_related("cities", "tours", "tours__images")
                .order_by("country_name")
            )
        return Country.objects.all().order_by("country_name")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CountryDetailSerializer
        return CountryListSerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["country"]

    def get_queryset(self):
        if self.action == "retrieve":
            return (
                City.objects
                .select_related("country")
                .prefetch_related("tours", "tours__images", "attractions__city__country")
                .order_by("city_name")
            )
        return City.objects.select_related("country").order_by("city_name")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CityDetailSerializer
        return CityListSerializer


class TourCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.action == "retrieve":
            return (
                TourCategory.objects
                .prefetch_related("tours", "tours__images")
                .order_by("name")
            )
        return TourCategory.objects.all().order_by("name")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TourCategoryDetailSerializer
        return TourCategoryListSerializer


# ========================
# TOURS
# ========================

class TourViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TourFilter
    search_fields = ["title", "description", "country__country_name", "city__city_name"]
    ordering_fields = ["created_at", "price", "duration_days"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base = (
            Tour.objects
            .filter(is_active=True)
            .select_related("country", "city")
            .order_by("-created_at")
        )
        if self.action == "retrieve":
            return base.prefetch_related(
                "categories", "images", "itinerary", "dates",
                "attractions__city__country", "price_tiers",
                "extra_services", "faqs", "route_points"
            )
        return base.prefetch_related("images", "dates", "attractions__city__country")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TourDetailSerializer
        return TourListSerializer


class TourDateUpcomingView(generics.ListAPIView):
    serializer_class = TourDateUpcomingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        today = timezone.now().date()
        return (
            TourDate.objects
            .filter(
                tour__is_active=True,
                tour__tour_type="group",
                start_date__gte=today,
                available_spots__gte=1
            )
            .select_related("tour", "tour__country")
            .prefetch_related("tour__images")
            .order_by("start_date")
        )


# ========================
# BOOKING
# ========================

class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        booking = serializer.save()
        if getattr(serializer, "is_duplicate", False):
            return
        try:
            send_booking_notification(booking)
        except Exception as e:
            logger.exception("Не удалось отправить уведомление о бронировании: %s", e)


# ========================
# QUIZ
# ========================

class QuizQuestionListView(generics.ListAPIView):
    serializer_class = QuizQuestionSerializer
    permission_classes = [AllowAny]
    queryset = (
        QuizQuestion.objects
        .filter(is_active=True)
        .prefetch_related("options")
        .order_by("order")
    )


class QuizLeadCreateView(generics.CreateAPIView):
    serializer_class = QuizLeadSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        quiz_lead = serializer.save()
        if getattr(serializer, "is_duplicate", False):
            return
        try:
            session_key = self.request.session.session_key
            if session_key:
                QuizProgress.objects.filter(
                    session_key=session_key,
                    is_completed=False
                ).update(is_completed=True)
            send_quiz_notification(quiz_lead)
        except Exception as e:
            logger.exception("Ошибка пост-обработки quiz lead: %s", e)


class QuizProgressView(generics.RetrieveAPIView):
    serializer_class = QuizProgressSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        if not self.request.session.session_key:
            self.request.session.create()
        progress, _ = QuizProgress.objects.get_or_create(
            session_key=self.request.session.session_key,
            is_completed=False,
            defaults={"answers": {}, "current_question_index": 0}
        )
        return progress


class QuizProgressUpdateView(generics.UpdateAPIView):
    serializer_class = QuizProgressUpdateSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        if not self.request.session.session_key:
            self.request.session.create()
        progress, _ = QuizProgress.objects.get_or_create(
            session_key=self.request.session.session_key,
            is_completed=False,
            defaults={"answers": {}, "current_question_index": 0}
        )
        return progress

    def update(self, request, *args, **kwargs):
        progress = self.get_object()
        serializer = self.get_serializer(progress, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuizProgressSerializer(progress).data, status=status.HTTP_200_OK)


# ========================
# ATTRACTIONS
# ========================

class AttractionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["city", "city__country"]
    search_fields = ["name", "description"]

    def get_queryset(self):
        base = (
            Attraction.objects
            .filter(is_active=True)
            .select_related("city", "city__country")
            .order_by("name")
        )
        if self.action == "retrieve":
            # tours__images — для TourShortSerializer.get_cover_image без N+1
            return base.prefetch_related("images", "tours__images")
        return base

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AttractionDetailSerializer
        return AttractionListSerializer


# ========================
# TRANSFER
# ========================

class TransferRouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        TransferRoute.objects
        .prefetch_related("vehicles")
        .order_by("departure_point", "arrival_point")
    )
    serializer_class = TransferRouteSerializer
    permission_classes = [AllowAny]


class TransportRequestCreateView(generics.CreateAPIView):
    serializer_class = TransportRequestCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        transport_request = serializer.save()
        if getattr(serializer, "is_duplicate", False):
            return
        try:
            # select_related чтобы избежать лишних запросов в send_transport_notification
            transport_request = (
                TransportRequest.objects
                .select_related("vehicle__route")
                .get(pk=transport_request.pk)
            )
            send_transport_notification(transport_request)
        except Exception as e:
            logger.exception("Не удалось отправить уведомление о трансфере: %s", e)


# ========================
# CONTACT
# ========================

class ContactRequestCreateView(generics.CreateAPIView):
    serializer_class = ContactRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        contact_request = serializer.save()
        if getattr(serializer, "is_duplicate", False):
            return
        try:
            send_contact_notification(contact_request)
        except Exception as e:
            logger.exception("Не удалось отправить уведомление о контакте: %s", e)