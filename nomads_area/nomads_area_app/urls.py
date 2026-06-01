from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    AttractionViewSet, BookingCreateView, CityViewSet, ContactRequestCreateView,
    CountryViewSet, FinikPayWebhookView, QuizLeadCreateView,
    QuizProgressStartView, QuizProgressUpdateView, QuizQuestionListView,
    SiteSettingsView, TeamMemberListView, TourCategoryViewSet, TourViewSet,
    TransferRouteListView, TransportRequestCreateView
)

router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="countries")
router.register(r"cities", CityViewSet, basename="cities")
router.register(r"categories", TourCategoryViewSet, basename="categories")
router.register(r"tours", TourViewSet, basename="tours")
router.register(r"attractions", AttractionViewSet, basename="attractions")

urlpatterns = [
    path("", include(router.urls)),
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("team/", TeamMemberListView.as_view(), name="team-list"),
    path("bookings/", BookingCreateView.as_view(), name="booking-create"),
    path("payments/finikpay/webhook/", FinikPayWebhookView.as_view(), name="finikpay-webhook"),
    path("quiz/questions/", QuizQuestionListView.as_view(), name="quiz-questions"),
    path("quiz/submit/", QuizLeadCreateView.as_view(), name="quiz-submit"),
    path("quiz/progress/", QuizProgressStartView.as_view(), name="quiz-progress"),
    path("quiz/progress/save/<str:session_key>/", QuizProgressUpdateView.as_view(), name="quiz-progress-save"),
    path("transfer-routes/", TransferRouteListView.as_view(), name="transfer-routes"),
    path("transport-requests/", TransportRequestCreateView.as_view(), name="transport-request-create"),
    path("contact/", ContactRequestCreateView.as_view(), name="contact-request"),
]