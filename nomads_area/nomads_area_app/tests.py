from datetime import date, timedelta
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (Attraction, Booking, City, ContactRequest, Country,
                     QuizAnswerOption, QuizLead, QuizProgress, QuizQuestion,
                     Tour, TourDate, TourPriceTier, TransferRoute,
                     TransportRequest, VehicleType)


class BaseNoSpamTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        self.patcher_throttle = patch(
            "nomads_area_app.throttles.FormSubmitThrottle.allow_request",
            return_value=True)
        self.patcher_tg = patch("nomads_area_app.tasks.send_telegram_task.delay")
        self.patcher_email = patch("nomads_area_app.tasks.send_email_task.delay")

        self.mock_allow = self.patcher_throttle.start()
        self.mock_tg = self.patcher_tg.start()
        self.mock_email = self.patcher_email.start()

    def tearDown(self):
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
            distance_km=250,
        )
        self.vehicle = VehicleType.objects.create(
            route=route,
            category="minivan",
            price=500,
            seats=6,
            bags=2,
        )

        self.booking_url = reverse("booking-create")
        self.transport_url = reverse("transport-request-create")
        self.contact_url = reverse("contact-request")
        self.quiz_submit_url = reverse("quiz-submit")
        self.quiz_progress_url = reverse("quiz-progress")
        self.quiz_progress_save_url = reverse("quiz-progress-save")
        self.quiz_questions_url = reverse("quiz-questions")
        self.tour_dates_upcoming_url = reverse("tour-dates-upcoming")

    def _reset_mocks(self):
        self.mock_tg.reset_mock()
        self.mock_email.reset_mock()

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
        self.assertEqual(response.data["price_per_person"], 100)
        self.assertEqual(response.data["total_price"], 200)
        self.assertEqual(response.data["deposit_amount"], 60)

        self.group_tour_date_available.refresh_from_db()
        self.assertEqual(self.group_tour_date_available.available_spots, 3)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_booking_overbooking_fails(self):
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
        self.assertIn("adults", response.data)

        self.group_tour_date_available.refresh_from_db()
        self.assertEqual(self.group_tour_date_available.available_spots, 5)

        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_private_tier_pricing(self):
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
        self.assertEqual(response.data["price_per_person"], 100)
        self.assertEqual(response.data["total_price"], 400)
        self.assertEqual(response.data["deposit_amount"], 120)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_booking_deduplication(self):
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

        self.assertEqual(Booking.objects.count(), 1)

        self.group_tour_date_available.refresh_from_db()
        self.assertEqual(self.group_tour_date_available.available_spots, 4)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_transport_create_and_dedup(self):
        self._reset_mocks()

        payload = {
            "vehicle": self.vehicle.id,
            "customer_phone": "+996555999888",
            "passengers": 2,
            "travel_date": date.today() + timedelta(days=30),
            "flight_number": "FL123",
            "customer_name": "Client",
            "luggage_count": 1,
            "comment": "Test",
        }

        response1 = self.client.post(self.transport_url, payload, format="json")
        response2 = self.client.post(self.transport_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        self.assertEqual(TransportRequest.objects.count(), 1)
        self.assertEqual(response1.data["total_price"], self.vehicle.price)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_contact_create_and_dedup(self):
        self._reset_mocks()

        payload = {
            "name": "Contact Name",
            "phone_or_email": "contact@test.com",
            "subject": "Hello",
            "message": "Message body",
            "source": "tour_page",
        }

        response1 = self.client.post(self.contact_url, payload, format="json")
        response2 = self.client.post(self.contact_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        self.assertEqual(ContactRequest.objects.count(), 1)

        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_quiz_questions_list_ok(self):
        QuizQuestion.objects.create(
            text="Q1",
            question_type="radio",
            order=1,
            is_active=True,
        )
        # опции не обязательны для 200, но добавим
        q = QuizQuestion.objects.get(text="Q1")
        QuizAnswerOption.objects.create(question=q, text="A1", order=1)

        response = self.client.get(self.quiz_questions_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_quiz_progress_flow(self):
        self._reset_mocks()

        response_get = self.client.get(self.quiz_progress_url)
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        self.assertIn("answers", response_get.data)
        self.assertIn("current_question_index", response_get.data)

        payload = {
            "answers": {"Q1": "A1"},
            "current_question_index": 1,
        }
        response_patch = self.client.patch(
            self.quiz_progress_save_url,
            payload,
            format="json"
        )
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(response_patch.data["current_question_index"], 1)

        self.assertTrue(QuizProgress.objects.exists())
        self.assertEqual(self.mock_tg.call_count, 0)

    def test_quiz_submit_and_dedup(self):
        self._reset_mocks()

        payload = {
            "name": "Quiz User",
            "phone_or_telegram": "tguser123",
            "answers": {"Q1": ["A1"], "Q2": "B1"},
        }

        response1 = self.client.post(self.quiz_submit_url, payload, format="json")
        response2 = self.client.post(self.quiz_submit_url, payload, format="json")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        self.assertEqual(QuizLead.objects.count(), 1)
        self.assertEqual(self.mock_tg.call_count, 1)
        self.assertEqual(self.mock_email.call_count, 1)

    def test_tour_filters_exclude_sold_out(self):
        self._reset_mocks()

        url = reverse("tours-list")
        response = self.client.get(url, {"exclude_sold_out": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data["results"]] \
            if isinstance(response.data, dict) and "results" in response.data \
            else [item["id"] for item in response.data]

        # Должны быть:
        # - self.group_tour (но только если есть доступные даты; т.к. у тура есть дата с доступными местами,
        #   тур включится в общий список один раз)
        # - self.private_tour (always included)
        self.assertIn(self.group_tour.id, ids)
        self.assertIn(self.private_tour.id, ids)

    def test_tour_dates_upcoming(self):
        response = self.client.get(self.tour_dates_upcoming_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data]

        # Дата available должна быть
        self.assertIn(self.group_tour_date_available.id, ids)
        # sold out date не должна быть
        self.assertNotIn(self.group_tour_date_sold_out.id, ids)

    # ========================
    # QUIZ QUESTIONS
    # ========================

    q1, _ = QuizQuestion.objects.get_or_create(
        text="Какой тип путешествия вам интересен?",
        defaults={"question_type": "radio", "order": 1, "is_active": True}
    )
    QuizAnswerOption.objects.get_or_create(question=q1, text="Горы и трекинг", defaults={"order": 1})
    QuizAnswerOption.objects.get_or_create(question=q1, text="Культура и города", defaults={"order": 2})
    QuizAnswerOption.objects.get_or_create(question=q1, text="Джип-тур", defaults={"order": 3})

    q2, _ = QuizQuestion.objects.get_or_create(
        text="Сколько человек поедет?",
        defaults={"question_type": "radio", "order": 2, "is_active": True}
    )
    QuizAnswerOption.objects.get_or_create(question=q2, text="1", defaults={"order": 1})
    QuizAnswerOption.objects.get_or_create(question=q2, text="2", defaults={"order": 2})
    QuizAnswerOption.objects.get_or_create(question=q2, text="3-4", defaults={"order": 3})
    QuizAnswerOption.objects.get_or_create(question=q2, text="5+", defaults={"order": 4})

    QuizQuestion.objects.get_or_create(
        text="Оставьте ваш контакт (WhatsApp/Telegram):",
        defaults={"question_type": "text", "order": 3, "is_active": True}
    )