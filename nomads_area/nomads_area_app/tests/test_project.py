from datetime import date, timedelta
from importlib import import_module

from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status

from .base import BaseNoSpamTestCase, API
from ..models import (
    Attraction, AttractionImage, Booking, City, ContactRequest, Country,
    QuizAnswerOption, QuizLead, QuizProgress, QuizQuestion,
    ExtraService, Tour, TourDate, TourPriceTier,
)
from ..admin import AttractionAdminForm


class ProjectTests(BaseNoSpamTestCase):
    """Основной набор интеграционных тестов бизнес-логики"""

    def setUp(self):
        super().setUp()

        # Создание базовой структуры данных
        self.country = Country.objects.create(country_name="Кыргызстан")
        self.city = City.objects.create(country=self.country, city_name="Бишкек")

        self.group_tour = Tour.objects.create(
            title="Group Tour Test",
            tour_type="group",
            country=self.country,
            city=self.city,
            duration_days=3,
            price=100,
            currency="USD",
            description="Test description",
            included="Всё включено",
            is_active=True,
        )

        self.group_tour_date_available = TourDate.objects.create(
            tour=self.group_tour,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=13),
            available_spots=5,
        )

        self.group_tour_date_sold_out = TourDate.objects.create(
            tour=self.group_tour,
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=23),
            available_spots=0,
        )

        self.private_tour = Tour.objects.create(
            title="Private Tour Test",
            tour_type="private",
            country=self.country,
            city=self.city,
            duration_days=1,
            price=300,
            currency="USD",
            description="Test description",
            included="Всё включено",
            is_active=True,
        )

        TourPriceTier.objects.create(
            tour=self.private_tour,
            min_people=1,
            max_people=2,
            price_per_person=150,
        )

        TourPriceTier.objects.create(
            tour=self.private_tour,
            min_people=3,
            max_people=None,
            price_per_person=100,
        )

        # URL-эндпоинты
        self.booking_url = f"{API}/bookings/"
        self.contact_url = f"{API}/contact/"
        self.quiz_submit_url = f"{API}/quiz/submit/"
        self.quiz_progress_url = f"{API}/quiz/progress/"
        self.quiz_questions_url = f"{API}/quiz/questions/"
        self.tours_url = f"{API}/tours/"
        self.attractions_url = f"{API}/attractions/"

    def _reset_mocks(self):
        self.mock_tg.reset_mock()
        self.mock_email.reset_mock()

    # --- БРОНИРОВАНИЯ ---

    def test_booking_group_success(self):
        self._reset_mocks()
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Иван Иванов",
            "customer_contact": "+996555123456",
            "adults": 2,
            "children": 0,
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["number_of_people"], 2)
        self.assertEqual(float(response.data["total_price"]), 200.0)
        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_booking_with_extra_services_success(self):
        service = ExtraService.objects.create(
            tour=self.group_tour, title="Service", price=50, currency="USD", is_active=True
        )
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Ivan",
            "customer_contact": "123",
            "adults": 2,
            "extra_services": [service.id],
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=response.data["id"])
        self.assertEqual(list(booking.extra_services.values_list("id", flat=True)), [service.id])

    def test_booking_rejects_inactive_tour(self):
        self.group_tour.is_active = False
        self.group_tour.save(update_fields=["is_active"])
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Ivan",
            "customer_contact": "123",
            "adults": 1,
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tour", response.data)

    def test_booking_rejects_extra_service_from_other_tour(self):
        service = ExtraService.objects.create(
            tour=self.private_tour, title="Other", price=80, currency="USD", is_active=True
        )
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Ivan",
            "customer_contact": "123",
            "adults": 1,
            "extra_services": [service.id],
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_overbooking_fails(self):
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Client",
            "customer_contact": "123",
            "adults": 10,
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_sold_out_date_fails(self):
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_sold_out.id,
            "customer_name": "Client",
            "customer_contact": "123",
            "adults": 1,
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_private_tier_pricing(self):
        self._reset_mocks()
        payload = {
            "tour": self.private_tour.id,
            "preferred_start_date": date.today() + timedelta(days=20),
            "preferred_end_date": date.today() + timedelta(days=25),
            "customer_name": "Family",
            "customer_contact": "123",
            "adults": 3,
            "children": 1,
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data["total_price"]), 400.0)

    def test_booking_private_small_group_tier(self):
        payload = {
            "tour": self.private_tour.id,
            "preferred_start_date": date.today() + timedelta(days=5),
            "preferred_end_date": date.today() + timedelta(days=8),
            "customer_name": "Couple",
            "customer_contact": "123",
            "adults": 2,
        }
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data["total_price"]), 300.0)

    def test_booking_group_without_date_fails(self):
        payload = {"tour": self.group_tour.id, "customer_name": "C", "customer_contact": "1", "adults": 1}
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_private_without_dates_fails(self):
        payload = {"tour": self.private_tour.id, "customer_name": "C", "customer_contact": "1", "adults": 1}
        response = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_deduplication(self):
        self._reset_mocks()
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Double",
            "customer_contact": "999",
            "adults": 1,
        }
        r1 = self.client.post(self.booking_url, payload, format="json")
        r2 = self.client.post(self.booking_url, payload, format="json")
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r1.data["id"], r2.data["id"])
        self.assertEqual(Booking.objects.count(), 1)

    def test_booking_changed_payload_is_not_duplicate(self):
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "C",
            "customer_contact": "999",
            "adults": 1,
        }
        r1 = self.client.post(self.booking_url, payload, format="json")
        payload["adults"] = 2
        r2 = self.client.post(self.booking_url, payload, format="json")
        self.assertNotEqual(r1.data["id"], r2.data["id"])
        self.assertEqual(Booking.objects.count(), 2)

    def test_booking_deduplication_expires_after_window(self):
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Returning",
            "customer_contact": "999",
            "adults": 1,
        }
        r1 = self.client.post(self.booking_url, payload, format="json")
        Booking.objects.filter(pk=r1.data["id"]).update(created_at=timezone.now() - timedelta(minutes=6))
        r2 = self.client.post(self.booking_url, payload, format="json")
        self.assertNotEqual(r1.data["id"], r2.data["id"])

    # --- КОНТАКТНЫЕ ЗАЯВКИ ---

    def test_contact_create_success(self):
        self._reset_mocks()
        payload = {"name": "Test", "phone_or_email": "t@t.com", "subject": "H", "message": "B", "source": "p"}
        response = self.client.post(self.contact_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactRequest.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)

    def test_contact_deduplication(self):
        payload = {"name": "Test", "phone_or_email": "t@t.com", "subject": "H", "message": "B"}
        self.client.post(self.contact_url, payload, format="json")
        self.client.post(self.contact_url, payload, format="json")
        self.assertEqual(ContactRequest.objects.count(), 1)

    def test_contact_changed_message_is_not_duplicate(self):
        payload = {"name": "T", "phone_or_email": "t@t.com", "message": "M1"}
        self.client.post(self.contact_url, payload, format="json")
        payload["message"] = "M2"
        self.client.post(self.contact_url, payload, format="json")
        self.assertEqual(ContactRequest.objects.count(), 2)

    # --- КВИЗ ---

    def test_quiz_questions_list(self):
        q = QuizQuestion.objects.create(question_text="?", question_type="single", order=1, is_active=True)
        QuizAnswerOption.objects.create(question=q, option_text="A")
        response = self.client.get(self.quiz_questions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_quiz_progress_start(self):
        response = self.client.post(self.quiz_progress_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(QuizProgress.objects.exists())

    def test_quiz_submit_success(self):
        self._reset_mocks()
        payload = {"customer_name": "Q", "customer_contact": "c", "answers_data": {"1": "A"}}
        response = self.client.post(self.quiz_submit_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuizLead.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)

    def test_quiz_submit_deduplication(self):
        payload = {"customer_name": "Q", "customer_contact": "c", "answers_data": {"1": "A"}}
        self.client.post(self.quiz_submit_url, payload, format="json")
        self.client.post(self.quiz_submit_url, payload, format="json")
        self.assertEqual(QuizLead.objects.count(), 1)

    def test_quiz_changed_answers_are_not_duplicate(self):
        payload = {"customer_name": "Q", "customer_contact": "c", "answers_data": {"1": "A"}}
        self.client.post(self.quiz_submit_url, payload, format="json")
        payload["answers_data"] = {"1": "B"}
        self.client.post(self.quiz_submit_url, payload, format="json")
        self.assertEqual(QuizLead.objects.count(), 2)

    # --- ФИЛЬТРЫ ТУРОВ ---

    def test_tour_list_returns_active_tours(self):
        inactive = Tour.objects.create(title="X", tour_type="group", country=self.country, city=self.city, duration_days=1, price=1, currency="USD", is_active=False)
        response = self.client.get(self.tours_url)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(inactive.id, ids)

    def test_tour_filter_exclude_sold_out(self):
        response = self.client.get(self.tours_url, {"exclude_sold_out": "true"})
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.group_tour.id, ids)

    # --- ДОСТОПРИМЕЧАТЕЛЬНОСТИ ---

    def test_attractions_can_be_filtered_by_country_id(self):
        k = Country.objects.create(country_name="K", country_name_en="Kazakhstan")
        c = City.objects.create(country=k, city_name="A")
        attr = Attraction.objects.create(city=c, name="Place", description="D", image="i.jpg", is_active=True)
        response = self.client.get(self.attractions_url, {"country": k.id})
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(attr.id, ids)

    def test_attraction_list_excludes_inactive_items(self):
        inactive = Attraction.objects.create(city=self.city, name="S", description="D", image="i.jpg", is_active=False)
        response = self.client.get(self.attractions_url)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(inactive.id, ids)

    def test_attractions_can_be_filtered_by_country_name(self):
        k = Country.objects.create(country_name="K", country_name_en="Kazakhstan")
        c = City.objects.create(country=k, city_name="A")
        attr = Attraction.objects.create(city=c, name="Place", description="D", image="i.jpg", is_active=True)
        response = self.client.get(self.attractions_url, {"country": "Kazakhstan"})
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [attr.id])

    def test_attraction_detail_returns_related_tours(self):
        attr = Attraction.objects.create(city=self.city, name="S", description="D", image="i.jpg", is_active=True)
        attr.tours.add(self.group_tour, self.private_tour)
        response = self.client.get(f"{self.attractions_url}{attr.id}/")
        tour_ids = {item["id"] for item in response.data["tours"]}
        self.assertEqual(tour_ids, {self.group_tour.id, self.private_tour.id})

    def test_attraction_admin_form_rejects_duplicate_in_same_city(self):
        Attraction.objects.create(city=self.city, name="B", description="D", image="i.jpg", is_active=True)
        form = AttractionAdminForm(data={"city": self.city.id, "name": "b", "description": "D", "is_active": True}, files={"image": SimpleUploadedFile("b.gif", b"GIF87a...", content_type="image/gif")})
        self.assertFalse(form.is_valid())
        self.assertIn("Такая достопримечательность уже есть", str(form.errors))

    def test_deduplicate_attractions_migration_merges_tours_and_gallery(self):
        f = Attraction.objects.create(city=self.city, name="B", description="D", image="i.jpg", is_active=True)
        s = Attraction.objects.create(city=self.city, name=" b ", description="D", image="i2.jpg", is_active=True)
        f.tours.add(self.group_tour)
        s.tours.add(self.private_tour)
        img = AttractionImage.objects.create(attraction=s, image="g.jpg", order=1)
        migration = import_module("nomads_area_app.migrations.0013_deduplicate_attractions")
        migration.merge_duplicate_attractions(apps, None)
        remaining = Attraction.objects.get(city=self.city, name="B")
        self.assertEqual(set(remaining.tours.values_list("id", flat=True)), {self.group_tour.id, self.private_tour.id})
        img.refresh_from_db()
        self.assertEqual(img.attraction_id, remaining.id)