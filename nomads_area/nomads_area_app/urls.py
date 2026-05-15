from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AttractionViewSet, BookingCreateView, CityViewSet, ContactRequestCreateView, CountryViewSet,
                    QuizLeadCreateView, QuizProgressUpdateView, QuizProgressView, QuizQuestionListView,
                    SiteSettingsView, TeamMemberListView, TourCategoryViewSet, TourDateUpcomingView, TourViewSet,
                    TransferRouteViewSet, TransportRequestCreateView, PaymentCreateView)


router = DefaultRouter()
router.register(r"countries", CountryViewSet, basename="countries")
router.register(r"cities", CityViewSet, basename="cities")
router.register(r"categories", TourCategoryViewSet, basename="categories")
router.register(r"tours", TourViewSet, basename="tours")
router.register(r"attractions", AttractionViewSet, basename="attractions")
router.register(r"transfer-routes", TransferRouteViewSet, basename="transfer-routes")


urlpatterns = [
    path("tour-dates/upcoming/", TourDateUpcomingView.as_view(), name="tour-dates-upcoming"),
    path("", include(router.urls)),
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("team/", TeamMemberListView.as_view(), name="team-list"),
    path("bookings/", BookingCreateView.as_view(), name="booking-create"),
    path("quiz/questions/", QuizQuestionListView.as_view(), name="quiz-questions"),
    path("quiz/submit/", QuizLeadCreateView.as_view(), name="quiz-submit"),
    path("quiz/progress/", QuizProgressView.as_view(), name="quiz-progress"),
    path("quiz/progress/save/", QuizProgressUpdateView.as_view(), name="quiz-progress-save"),
    path("transport-requests/", TransportRequestCreateView.as_view(), name="transport-request-create"),
    path("contact/", ContactRequestCreateView.as_view(), name="contact-request"),
    path("payments/", PaymentCreateView.as_view(), name="payment-create"),
]