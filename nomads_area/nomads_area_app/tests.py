import hashlib
import hmac
import json
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import close_old_connections, connections
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .notifications import enqueue_task_safely
from .services import (
    create_booking_with_payment_service,
    create_contact_request_service,
    create_quiz_lead_service,
)
from .throttles import FormSubmitThrottle
from .models import (
    Booking, City, ContactRequest, Country,
    Payment, QuizAnswerOption, QuizLead, QuizProgress, QuizQuestion,
    ExtraService, Tour, TourDate, TourPriceTier,
)

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
        self.webhook_url = f"{API}/payments/finikpay/webhook/"

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

    def _signed_webhook(self, payload, secret="test-webhook-secret"):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return self.client.generic(
            "POST",
            self.webhook_url,
            body,
            content_type="application/json",
            HTTP_X_FINIKPAY_SIGNATURE=signature,
        )

    @override_settings(FINIKPAY_WEBHOOK_SECRET="test-webhook-secret")
    def test_paid_webhook_is_idempotent(self):
        booking_response = self.client.post(
            self.booking_url,
            {
                "tour": self.group_tour.id,
                "tour_date": self.group_tour_date_available.id,
                "customer_name": "Paid Client",
                "customer_contact": "+996700123456",
                "adults": 2,
                "children": 0,
            },
            format="json",
        )
        payment = Payment.objects.get(pk=booking_response.data["payment"]["id"])
        self._reset_mocks()
        payload = {
            "reference_id": str(payment.id),
            "id": payment.provider_payment_id,
            "status": "paid",
        }

        first = self._signed_webhook(payload)
        second = self._signed_webhook(payload)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data["changed"])
        self.assertFalse(second.data["changed"])
        self.group_tour_date_available.refresh_from_db()
        self.assertEqual(self.group_tour_date_available.available_spots, 3)
        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    @override_settings(FINIKPAY_WEBHOOK_SECRET="test-webhook-secret")
    def test_webhook_rejects_invalid_signature(self):
        response = self.client.post(
            self.webhook_url,
            {"reference_id": "1", "status": "paid"},
            format="json",
            HTTP_X_FINIKPAY_SIGNATURE="invalid",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(FINIKPAY_WEBHOOK_SECRET="test-webhook-secret")
    def test_webhook_rejects_provider_payment_id_mismatch(self):
        booking_response = self.client.post(
            self.booking_url,
            {
                "tour": self.group_tour.id,
                "tour_date": self.group_tour_date_available.id,
                "customer_name": "Mismatch Client",
                "customer_contact": "+996700123457",
                "adults": 1,
                "children": 0,
            },
            format="json",
        )
        payment = Payment.objects.get(pk=booking_response.data["payment"]["id"])

        response = self._signed_webhook({
            "reference_id": str(payment.id),
            "id": "different-provider-id",
            "status": "paid",
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

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
            with patch("nomads_area_app.services.get_payment_provider") as provider:
                provider.return_value.create_payment.return_value = {
                    "provider_payment_id": "",
                    "payment_url": "",
                }
                booking, payment, duplicate = create_booking_with_payment_service(
                    data,
                    tour_date=tour_date,
                )
            return booking.pk, payment.pk, duplicate
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
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(sorted(result[2] for result in results), [False, True])

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

    def test_concurrent_payments_cannot_overbook(self):
        _, first_payment_id, _ = self._create_booking("+996700000001", 3)
        _, second_payment_id, _ = self._create_booking("+996700000002", 3)
        barrier = Barrier(2)

        def pay(payment_id):
            close_old_connections()
            try:
                barrier.wait()
                payment = Payment.objects.get(pk=payment_id)
                try:
                    payment.mark_paid_and_confirm_booking({"status": "paid"})
                    return "paid"
                except DjangoValidationError:
                    return "rejected"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(pay, [first_payment_id, second_payment_id]))

        self.tour_date.refresh_from_db()
        self.assertEqual(sorted(outcomes), ["paid", "rejected"])
        self.assertEqual(self.tour_date.available_spots, 2)
        self.assertEqual(Payment.objects.filter(status=Payment.STATUS_PAID).count(), 1)

    def test_payment_state_transitions_are_idempotent(self):
        _, payment_id, _ = self._create_booking("+996700000003", 1)
        payment = Payment.objects.get(pk=payment_id)

        _, changed_first = payment.mark_failed({"status": "failed"})
        _, changed_second = payment.mark_failed({"status": "failed"})

        self.assertTrue(changed_first)
        self.assertFalse(changed_second)
        with self.assertRaises(DjangoValidationError):
            payment.mark_paid_and_confirm_booking({"status": "paid"})
