from datetime import date, timedelta
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Booking, City, ContactRequest, Country,
    QuizAnswerOption, QuizLead, QuizProgress, QuizQuestion,
    ExtraService, Tour, TourDate, TourPriceTier, TransferRoute,
    TransportRequest, VehicleType,
)

LANG = "ru"
API = f"/api/{LANG}"


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

        route = TransferRoute.objects.create(
            departure_point="Bishkek",
            arrival_point="Karakol",
        )
        self.vehicle = VehicleType.objects.create(
            route=route,
            category="minivan",
            price=500,
            seats=6,
            bags=2,
        )

        self.booking_url = f"{API}/bookings/"
        self.transport_url = f"{API}/transport-requests/"
        self.contact_url = f"{API}/contact/"
        self.quiz_submit_url = f"{API}/quiz/submit/"
        self.quiz_progress_url = f"{API}/quiz/progress/"
        self.quiz_questions_url = f"{API}/quiz/questions/"
        self.tours_url = f"{API}/tours/"

    def _reset_mocks(self):
        self.mock_tg.reset_mock()
        self.mock_email.reset_mock()

    # ------------------------------------------------------------------ #
    # БРОНИРОВАНИЯ                                                         #
    # ------------------------------------------------------------------ #

    def test_booking_group_success(self):
        """Групповое бронирование создаётся, цена и предоплата считаются правильно."""
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
        self.assertEqual(float(response.data["prepayment_amount"]), 60.0)

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
        self.assertEqual(float(response.data["prepayment_amount"]), 120.0)

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

    # ------------------------------------------------------------------ #
    # ТРАНСФЕРЫ                                                            #
    # ------------------------------------------------------------------ #

    def test_transport_create_success(self):
        """Заявка на трансфер создаётся, цена берётся из автомобиля."""
        self._reset_mocks()

        payload = {
            "vehicle": self.vehicle.id,
            "customer_phone": "+996555999888",
            "customer_name": "Client",
            "passengers": 2,
            "bags": 1,
            "comment": "Test",
        }

        response = self.client.post(self.transport_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransportRequest.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_transport_deduplication(self):
        """Два одинаковых запроса — создаётся одна заявка."""
        self._reset_mocks()

        payload = {
            "vehicle": self.vehicle.id,
            "customer_phone": "+996555999888",
            "customer_name": "Client",
            "passengers": 2,
            "bags": 1,
        }

        response1 = self.client.post(self.transport_url, payload, format="json")
        response2 = self.client.post(self.transport_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransportRequest.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)

    def test_transport_overbooking_passengers_fails(self):
        """Пассажиров больше чем мест в авто — ошибка."""
        payload = {
            "vehicle": self.vehicle.id,
            "customer_phone": "+996555000001",
            "passengers": 10,
            "bags": 0,
        }

        response = self.client.post(self.transport_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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