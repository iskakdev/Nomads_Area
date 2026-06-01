import logging
from datetime import date
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import TourFilter
from .models import (
    Attraction, City, Country, QuizProgress, QuizQuestion, SiteSettings,
    TeamMember, Tour, TourCategory, TourDate, TransferRoute, TransportRequest, Payment
)
from .notifications import (
    send_booking_notification, send_contact_notification,
    send_quiz_notification, send_transport_notification, send_payment_success_notification
)
from .payment_providers import PaymentProviderError, PaymentVerificationError, get_payment_provider
from .serializers import (
    AttractionDetailSerializer, AttractionListSerializer, BookingCreateSerializer,
    CityDetailSerializer, CityListSerializer, ContactRequestSerializer,
    CountryDetailSerializer, CountryListSerializer, QuizLeadSerializer,
    QuizProgressSerializer, QuizProgressUpdateSerializer, QuizQuestionSerializer,
    SiteSettingsSerializer, TeamMemberSerializer, TourCategoryDetailSerializer,
    TourCategoryListSerializer, TourDetailSerializer, TourListSerializer,
    TransferRouteSerializer, TransportRequestCreateSerializer
)
from .services import handle_payment_webhook_service, update_quiz_progress_service
from .throttles import FormSubmitThrottle

logger = logging.getLogger(__name__)


class SiteSettingsView(generics.RetrieveAPIView):
    serializer_class = SiteSettingsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return SiteSettings.get_settings()


class TeamMemberListView(generics.ListAPIView):
    queryset = TeamMember.objects.filter(is_active=True)
    serializer_class = TeamMemberSerializer
    permission_classes = [AllowAny]


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Country.objects.prefetch_related("cities", "tours")

    def get_serializer_class(self):
        return CountryDetailSerializer if self.action == "retrieve" else CountryListSerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return City.objects.select_related("country").prefetch_related("tours")

    def get_serializer_class(self):
        return CityDetailSerializer if self.action == "retrieve" else CityListSerializer


class TourCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return (
            TourCategory.objects.filter(is_active=True)
            .prefetch_related("tours")
            .annotate(tours_count=Count("tours", filter=Q(tours__is_active=True)))
            .order_by("-tours_count", "order", "id")
        )

    def get_serializer_class(self):
        return TourCategoryDetailSerializer if self.action == "retrieve" else TourCategoryListSerializer


class TourViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = TourFilter
    search_fields = ["title", "description", "city__city_name"]
    ordering_fields = ["price", "duration_days", "created_at"]

    def get_queryset(self):
        today = date.today()
        base = Tour.objects.filter(is_active=True).select_related("country", "city").prefetch_related("images")
        dates_p = Prefetch(
            "dates",
            queryset=TourDate.objects.filter(start_date__gte=today).order_by("start_date"),
            to_attr="prefetched_dates",
        )
        if self.action == "retrieve":
            return base.prefetch_related("itinerary_days", "faqs", "extra_services", "route_points", "price_tiers", "attractions", dates_p)
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


class FinikPayWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        provider = get_payment_provider()
        sig = request.headers.get("X-Finikpay-Signature") or request.headers.get("X-Signature")
        if not provider.verify_webhook_signature(request.body, sig):
            raise PermissionDenied("Invalid signature.")

        try:
            result = handle_payment_webhook_service(request.data)
        except (PaymentVerificationError, PaymentProviderError, DjangoValidationError) as e:
            raise ValidationError({"detail": str(e)}) from e

        if result["changed"] and result["payment"].status == Payment.STATUS_PAID:
            transaction.on_commit(lambda: send_payment_success_notification(result["payment"]))

        return Response({
            "status": "ok",
            "payment_id": result["payment"].id,
            "payment_status": result["payment"].status,
            "changed": result["changed"],
        }, status=status.HTTP_200_OK)


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


class AttractionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Attraction.objects.filter(is_active=True).select_related("city").prefetch_related("images", "tours")

    def get_serializer_class(self):
        return AttractionDetailSerializer if self.action == "retrieve" else AttractionListSerializer


class TransferRouteListView(generics.ListAPIView):
    queryset = TransferRoute.objects.prefetch_related("vehicles").all()
    serializer_class = TransferRouteSerializer
    permission_classes = [AllowAny]


class TransportRequestCreateView(generics.CreateAPIView):
    serializer_class = TransportRequestCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        instance = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_transport_notification(instance))


class ContactRequestCreateView(generics.CreateAPIView):
    serializer_class = ContactRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        instance = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_contact_notification(instance))
