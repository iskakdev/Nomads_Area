from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from threading import Barrier
from unittest.mock import patch

from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connections
from django.test import SimpleTestCase, TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .notifications import enqueue_task_safely
from .services import (
    create_booking_service,
    create_contact_request_service,
    create_quiz_lead_service,
)
from .throttles import FormSubmitThrottle
from .models import (
    Attraction, AttractionImage, Booking, City, ContactRequest, Country,
    QuizAnswerOption, QuizLead, QuizProgress, QuizQuestion,
    ExtraService, Tour, TourDate, TourPriceTier,
)
from .admin import AttractionAdminForm

LANG = "ru"
API = f"/api/{LANG}"


class FormSubmitThrottleTests(SimpleTestCase):
    def test_rate_comes_from_drf_settings(self):
        with patch.dict(FormSubmitThrottle.THROTTLE_RATES, {"forms": "17/minute"}):
            self.assertEqual(FormSubmitThrottle().get_rate(), "17/minute")


class NotificationSafetyTests(SimpleTestCase):
    def test_enqueue_failure_is_swallowed(self):
        task = type("Task", (), {"name": "broken", "delay": lambda self, *args: (_ for _ in ()).throw(ConnectionError("down"))})()

        with self.assertLogs("nomads_area_app.notifications", level="ERROR"):
            result = enqueue_task_safely(task, "payload")

        self.assertIsNone(result)


class BaseNoSpamTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.patcher_throttle = patch(
            "nomads_area_app.throttles.FormSubmitThrottle.allow_request",
            return_value=True,
        )
        # Патчим delay в tasks, а on_commit заменяем чтобы вызывался сразу
        self.patcher_tg = patch("nomads_area_app.tasks.send_telegram_task.delay")
        self.patcher_email = patch("nomads_area_app.tasks.send_email_task.delay")
        self.patcher_on_commit = patch(
            "django.db.transaction.on_commit",
            side_effect=lambda fn: fn(),
        )

        self.mock_allow = self.patcher_throttle.start()
        self.mock_tg = self.patcher_tg.start()
        self.mock_email = self.patcher_email.start()
        self.mock_on_commit = self.patcher_on_commit.start()

    def tearDown(self):
        self.patcher_on_commit.stop()
        self.patcher_email.stop()
        self.patcher_tg.stop()
        self.patcher_throttle.stop()
        super().tearDown()


class ProjectTests(BaseNoSpamTestCase):
    def setUp(self):
        super().setUp()

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

    # ------------------------------------------------------------------ #
    # БРОНИРОВАНИЯ                                                         #
    # ------------------------------------------------------------------ #

    def test_booking_group_success(self):
        """Групповое бронирование создаётся, цена считается правильно."""
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
        self.assertEqual(float(response.data["price_per_person"]), 100.0)
        self.assertEqual(float(response.data["total_price"]), 200.0)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_booking_with_extra_services_success(self):
        """Выбранные extra services сохраняются вместе с бронью."""
        service = ExtraService.objects.create(
            tour=self.group_tour,
            title="Дрон DJI Mini 3 Pro",
            price=50,
            currency="USD",
            is_active=True,
        )
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Иван Иванов",
            "customer_contact": "+996555123456",
            "adults": 2,
            "children": 0,
            "extra_services": [service.id],
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        booking = Booking.objects.get(pk=response.data["id"])
        self.assertEqual(list(booking.extra_services.values_list("id", flat=True)), [service.id])
        self.assertEqual(response.data["extra_services"], [service.id])

    def test_booking_rejects_inactive_tour(self):
        """Скрытый тур нельзя забронировать даже если страница осталась в кеше."""
        self.group_tour.is_active = False
        self.group_tour.save(update_fields=["is_active"])

        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Иван Иванов",
            "customer_contact": "+996555123456",
            "adults": 2,
            "children": 0,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tour", response.data)
        self.assertEqual(Booking.objects.count(), 0)
        self.assertEqual(self.mock_tg.call_count, 0)
        self.assertEqual(self.mock_email.call_count, 0)

    def test_booking_rejects_extra_service_from_other_tour(self):
        """Extra service нельзя прикрепить к броне другого тура."""
        service = ExtraService.objects.create(
            tour=self.private_tour,
            title="Чужая услуга",
            price=80,
            currency="USD",
            is_active=True,
        )
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Иван Иванов",
            "customer_contact": "+996555123456",
            "adults": 2,
            "children": 0,
            "extra_services": [service.id],
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_overbooking_fails(self):
        """Нельзя забронировать больше мест чем доступно."""
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Жадный Клиент",
            "customer_contact": "+996500000000",
            "adults": 10,
            "children": 0,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.group_tour_date_available.refresh_from_db()
        self.assertEqual(self.group_tour_date_available.available_spots, 5)
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_sold_out_date_fails(self):
        """Нельзя забронировать дату с нулём мест."""
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_sold_out.id,
            "customer_name": "Клиент",
            "customer_contact": "+996500000001",
            "adults": 1,
            "children": 0,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_private_tier_pricing(self):
        """Приватный тур — цена берётся из тира по количеству людей."""
        self._reset_mocks()

        payload = {
            "tour": self.private_tour.id,
            "preferred_start_date": date.today() + timedelta(days=20),
            "preferred_end_date": date.today() + timedelta(days=25),
            "customer_name": "Семья",
            "customer_contact": "+996700111222",
            "adults": 3,
            "children": 1,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["number_of_people"], 4)
        self.assertEqual(float(response.data["price_per_person"]), 100.0)
        self.assertEqual(float(response.data["total_price"]), 400.0)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_booking_private_small_group_tier(self):
        """Приватный тур 1-2 человека — берётся первый тир (150$/чел)."""
        payload = {
            "tour": self.private_tour.id,
            "preferred_start_date": date.today() + timedelta(days=5),
            "preferred_end_date": date.today() + timedelta(days=8),
            "customer_name": "Пара",
            "customer_contact": "+996700000001",
            "adults": 2,
            "children": 0,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data["price_per_person"]), 150.0)
        self.assertEqual(float(response.data["total_price"]), 300.0)

    def test_booking_group_without_date_fails(self):
        """Групповой тур без даты — ошибка валидации."""
        payload = {
            "tour": self.group_tour.id,
            "customer_name": "Клиент",
            "customer_contact": "+996500000002",
            "adults": 1,
            "children": 0,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_private_without_dates_fails(self):
        """Приватный тур без желаемых дат — ошибка валидации."""
        payload = {
            "tour": self.private_tour.id,
            "customer_name": "Клиент",
            "customer_contact": "+996500000003",
            "adults": 1,
            "children": 0,
        }

        response = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_deduplication(self):
        """Два одинаковых запроса подряд — создаётся одна бронь."""
        self._reset_mocks()

        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Дубль",
            "customer_contact": "+996900123123",
            "adults": 1,
            "children": 0,
        }

        response1 = self.client.post(self.booking_url, payload, format="json")
        response2 = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data["id"], response2.data["id"])

        self.assertEqual(Booking.objects.count(), 1)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_booking_changed_payload_is_not_duplicate(self):
        """Тот же клиент может создать другую бронь в течение пяти минут."""
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Повторный клиент",
            "customer_contact": "+996900123123",
            "adults": 1,
            "children": 0,
        }

        first = self.client.post(self.booking_url, payload, format="json")
        payload["adults"] = 2
        second = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first.data["id"], second.data["id"])
        self.assertEqual(Booking.objects.count(), 2)
        self.assertEqual(self.mock_tg.call_count, 2)

    def test_booking_deduplication_expires_after_window(self):
        payload = {
            "tour": self.group_tour.id,
            "tour_date": self.group_tour_date_available.id,
            "customer_name": "Returning Client",
            "customer_contact": "+996900123124",
            "adults": 1,
            "children": 0,
        }

        first = self.client.post(self.booking_url, payload, format="json")
        Booking.objects.filter(pk=first.data["id"]).update(
            created_at=timezone.now() - timedelta(minutes=6)
        )
        second = self.client.post(self.booking_url, payload, format="json")

        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(first.data["id"], second.data["id"])
        self.assertEqual(Booking.objects.count(), 2)

    # ------------------------------------------------------------------ #
    # КОНТАКТНЫЕ ЗАЯВКИ                                                    #
    # ------------------------------------------------------------------ #

    def test_contact_create_success(self):
        """Контактная заявка создаётся."""
        self._reset_mocks()

        payload = {
            "name": "Contact Name",
            "phone_or_email": "contact@test.com",
            "subject": "Hello",
            "message": "Message body",
            "source": "tour_page",
        }

        response = self.client.post(self.contact_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactRequest.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_contact_deduplication(self):
        """Два одинаковых обращения — создаётся одно."""
        self._reset_mocks()

        payload = {
            "name": "Contact Name",
            "phone_or_email": "contact@test.com",
            "subject": "Hello",
            "message": "Message body",
        }

        response1 = self.client.post(self.contact_url, payload, format="json")
        response2 = self.client.post(self.contact_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactRequest.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)

    def test_contact_changed_message_is_not_duplicate(self):
        payload = {
            "name": "Contact Name",
            "phone_or_email": "contact@test.com",
            "subject": "Hello",
            "message": "First message",
        }

        first = self.client.post(self.contact_url, payload, format="json")
        payload["message"] = "Second message"
        second = self.client.post(self.contact_url, payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContactRequest.objects.count(), 2)

    # ------------------------------------------------------------------ #
    # КВИЗ                                                                 #
    # ------------------------------------------------------------------ #

    def test_quiz_questions_list(self):
        """Список вопросов квиза возвращается."""
        q = QuizQuestion.objects.create(
            question_text="Какой тип тура?",
            question_type="single",
            order=1,
            is_active=True,
        )
        QuizAnswerOption.objects.create(question=q, option_text="Горы")

        response = self.client.get(self.quiz_questions_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_quiz_progress_start(self):
        """Старт квиза создаёт прогресс."""
        response = self.client.post(self.quiz_progress_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(QuizProgress.objects.exists())

    def test_quiz_submit_success(self):
        """Лид из квиза создаётся."""
        self._reset_mocks()

        payload = {
            "customer_name": "Quiz User",
            "customer_contact": "tguser123",
            "answers_data": {"1": "Горы"},
        }

        response = self.client.post(self.quiz_submit_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuizLead.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_quiz_submit_deduplication(self):
        """Два одинаковых лида — создаётся один."""
        self._reset_mocks()

        payload = {
            "customer_name": "Quiz User",
            "customer_contact": "tguser123",
            "answers_data": {"1": "Горы"},
        }

        response1 = self.client.post(self.quiz_submit_url, payload, format="json")
        response2 = self.client.post(self.quiz_submit_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuizLead.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)

    def test_quiz_changed_answers_are_not_duplicate(self):
        payload = {
            "customer_name": "Quiz User",
            "customer_contact": "tguser123",
            "answers_data": {"Region": "Kyrgyzstan"},
        }

        first = self.client.post(self.quiz_submit_url, payload, format="json")
        payload["answers_data"] = {"Region": "Uzbekistan"}
        second = self.client.post(self.quiz_submit_url, payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuizLead.objects.count(), 2)

    # ------------------------------------------------------------------ #
    # ФИЛЬТРЫ ТУРОВ                                                        #
    # ------------------------------------------------------------------ #

    def test_tour_list_returns_active_tours(self):
        """Список туров возвращает только активные."""
        inactive_tour = Tour.objects.create(
            title="Inactive Tour",
            tour_type="group",
            country=self.country,
            city=self.city,
            duration_days=1,
            price=50,
            currency="USD",
            description="desc",
            included="incl",
            is_active=False,
        )

        response = self.client.get(self.tours_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(inactive_tour.id, ids)

    def test_tour_filter_exclude_sold_out(self):
        """Фильтр exclude_sold_out скрывает туры без мест."""
        response = self.client.get(self.tours_url, {"exclude_sold_out": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]

        self.assertIn(self.group_tour.id, ids)
        self.assertIn(self.private_tour.id, ids)

    # ------------------------------------------------------------------ #
    # ДОСТОПРИМЕЧАТЕЛЬНОСТИ                                               #
    # ------------------------------------------------------------------ #

    def test_attractions_can_be_filtered_by_country_id(self):
        """Страница достопримечательностей может показать только выбранную страну."""
        kazakhstan = Country.objects.create(country_name="Казахстан", country_name_en="Kazakhstan")
        almaty = City.objects.create(country=kazakhstan, city_name="Алматы", city_name_en="Almaty")

        kyrgyz_attraction = Attraction.objects.create(
            city=self.city,
            name="Ала-Арча",
            description="Горы Кыргызстана",
            image="attractions/ala-archa.jpg",
            is_active=True,
        )
        kazakh_attraction = Attraction.objects.create(
            city=almaty,
            name="Чарын",
            description="Каньон в Казахстане",
            image="attractions/charyn.jpg",
            is_active=True,
        )

        response = self.client.get(self.attractions_url, {"country": kazakhstan.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(kazakh_attraction.id, ids)
        self.assertNotIn(kyrgyz_attraction.id, ids)

    def test_attraction_list_excludes_inactive_items(self):
        """Неактивная достопримечательность не должна попадать на сайт."""
        active_attraction = Attraction.objects.create(
            city=self.city,
            name="Активное место",
            description="Показываем",
            image="attractions/active.jpg",
            is_active=True,
        )
        inactive_attraction = Attraction.objects.create(
            city=self.city,
            name="Скрытое место",
            description="Не показываем",
            image="attractions/inactive.jpg",
            is_active=False,
        )

        response = self.client.get(self.attractions_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(active_attraction.id, ids)
        self.assertNotIn(inactive_attraction.id, ids)

    def test_attractions_can_be_filtered_by_country_name(self):
        """Фильтр страны принимает не только id, но и название из маршрута."""
        kazakhstan = Country.objects.create(country_name="Казахстан", country_name_en="Kazakhstan")
        almaty = City.objects.create(country=kazakhstan, city_name="Алматы", city_name_en="Almaty")
        kazakh_attraction = Attraction.objects.create(
            city=almaty,
            name="Медеу",
            description="Каток в Алматы",
            image="attractions/medeu.jpg",
            is_active=True,
        )

        response = self.client.get(self.attractions_url, {"country": "Kazakhstan"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [kazakh_attraction.id])

    def test_attraction_detail_returns_related_tours(self):
        """Одна достопримечательность может быть связана с несколькими турами."""
        attraction = Attraction.objects.create(
            city=self.city,
            name="Сон-Куль",
            description="Озеро",
            image="attractions/son-kul.jpg",
            is_active=True,
        )
        attraction.tours.add(self.group_tour, self.private_tour)

        response = self.client.get(f"{self.attractions_url}{attraction.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tour_ids = {item["id"] for item in response.data["tours"]}
        self.assertEqual(tour_ids, {self.group_tour.id, self.private_tour.id})

    def test_attraction_admin_form_rejects_duplicate_in_same_city(self):
        """Менеджер не должен случайно создать дубль той же достопримечательности."""
        Attraction.objects.create(
            city=self.city,
            name="Байтерек",
            description="Существующая запись",
            image="attractions/baiterek.jpg",
            is_active=True,
        )

        form = AttractionAdminForm(data={
            "city": self.city.id,
            "name": "байтерек",
            "description": "Дубль",
            "is_active": True,
        }, files={
            "image": SimpleUploadedFile(
                "baiterek.gif",
                b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
                content_type="image/gif",
            ),
        })

        self.assertFalse(form.is_valid())
        self.assertIn("Такая достопримечательность уже есть", str(form.errors))

    def test_deduplicate_attractions_migration_merges_tours_and_gallery(self):
        """Data migration оставляет одну запись и переносит туры/галерею."""
        first = Attraction.objects.create(
            city=self.city,
            name="Baiterek",
            description="Основная запись",
            image="attractions/baiterek.jpg",
            is_active=True,
        )
        second = Attraction.objects.create(
            city=self.city,
            name="  baiterek  ",
            description="Дубль",
            image="attractions/baiterek-duplicate.jpg",
            is_active=True,
        )
        first.tours.add(self.group_tour)
        second.tours.add(self.private_tour)
        image = AttractionImage.objects.create(
            attraction=second,
            image="attractions/gallery/baiterek.jpg",
            alt_text="Baiterek",
            order=1,
        )

        migration = import_module("nomads_area_app.migrations.0013_deduplicate_attractions")
        migration.merge_duplicate_attractions(apps, None)

        remaining = Attraction.objects.get(city=self.city, name="Baiterek")
        self.assertEqual(Attraction.objects.filter(city=self.city, name__iexact="baiterek").count(), 1)
        self.assertEqual(set(remaining.tours.values_list("id", flat=True)), {self.group_tour.id, self.private_tour.id})
        image.refresh_from_db()
        self.assertEqual(image.attraction_id, remaining.id)


class ConcurrentIntegrityTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.country = Country.objects.create(country_name="Кыргызстан")
        self.city = City.objects.create(country=self.country, city_name="Бишкек")
        self.tour = Tour.objects.create(
            title="Concurrent Tour",
            tour_type="group",
            country=self.country,
            city=self.city,
            duration_days=3,
            price=100,
            currency="USD",
            description="Test",
            included="Test",
            is_active=True,
        )
        self.tour_date = TourDate.objects.create(
            tour=self.tour,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=13),
            available_spots=5,
        )
    def _create_booking(self, contact, adults):
        close_old_connections()
        try:
            tour = Tour.objects.get(pk=self.tour.pk)
            tour_date = TourDate.objects.get(pk=self.tour_date.pk)
            data = {
                "tour": tour,
                "tour_date": tour_date,
                "customer_name": "Concurrent Client",
                "customer_contact": contact,
                "adults": adults,
                "children": 0,
                "comment": "",
            }
            booking, duplicate = create_booking_service(data, tour_date=tour_date)
            return booking.pk, duplicate
        finally:
            connections.close_all()

    def test_concurrent_identical_bookings_create_one_row(self):
        barrier = Barrier(2)

        def submit():
            barrier.wait()
            return self._create_booking("+996700000000", 1)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: submit(), range(2)))

        self.assertEqual({result[0] for result in results}, {Booking.objects.get().pk})
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(sorted(result[1] for result in results), [False, True])

    def _run_concurrently(self, callback):
        barrier = Barrier(2)

        def submit():
            close_old_connections()
            try:
                barrier.wait()
                return callback()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            return list(executor.map(lambda _: submit(), range(2)))

    def test_concurrent_quiz_leads_create_one_row(self):
        results = self._run_concurrently(lambda: create_quiz_lead_service({
            "customer_name": "Quiz Client",
            "customer_contact": "@quiz-client",
            "answers_data": {"Region": "Kyrgyzstan"},
        }))

        self.assertEqual(QuizLead.objects.count(), 1)
        self.assertEqual({lead.pk for lead, _ in results}, {QuizLead.objects.get().pk})
        self.assertEqual(sorted(duplicate for _, duplicate in results), [False, True])

    def test_concurrent_contact_requests_create_one_row(self):
        results = self._run_concurrently(lambda: create_contact_request_service({
            "name": "Contact Client",
            "phone_or_email": "client@example.com",
            "subject": "Question",
            "message": "Same message",
            "source": "tour_page",
        }))

        self.assertEqual(ContactRequest.objects.count(), 1)
        self.assertEqual({request.pk for request, _ in results}, {ContactRequest.objects.get().pk})
        self.assertEqual(sorted(duplicate for _, duplicate in results), [False, True])

    def test_concurrent_confirmations_cannot_overbook(self):
        first_booking_id, _ = self._create_booking("+996700000001", 3)
        second_booking_id, _ = self._create_booking("+996700000002", 3)
        barrier = Barrier(2)

        def confirm(booking_id):
            close_old_connections()
            try:
                barrier.wait()
                booking = Booking.objects.get(pk=booking_id)
                try:
                    booking.confirm_and_reserve()
                    return "confirmed"
                except DjangoValidationError:
                    return "rejected"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(confirm, [first_booking_id, second_booking_id]))

        self.tour_date.refresh_from_db()
        self.assertEqual(sorted(outcomes), ["confirmed", "rejected"])
        self.assertEqual(self.tour_date.available_spots, 2)
        self.assertEqual(Booking.objects.filter(status=Booking.STATUS_CONFIRMED).count(), 1)

    def test_booking_confirmation_is_idempotent(self):
        booking_id, _ = self._create_booking("+996700000003", 1)
        booking = Booking.objects.get(pk=booking_id)

        booking.confirm_and_reserve()
        booking.confirm_and_reserve()

        self.tour_date.refresh_from_db()
        self.assertEqual(self.tour_date.available_spots, 4)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)

    def test_confirmed_booking_cancellation_restores_spots_once(self):
        booking_id, _ = self._create_booking("+996700000004", 2)
        booking = Booking.objects.get(pk=booking_id)

        booking.confirm_and_reserve()
        booking.cancel()
        booking.cancel()

        self.tour_date.refresh_from_db()
        self.assertEqual(self.tour_date.available_spots, 5)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)
