from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import close_old_connections, connections
from django.test import TransactionTestCase

from ..services import (
    create_booking_service,
    create_contact_request_service,
    create_quiz_lead_service,
)
from ..models import (
    Booking, City, ContactRequest, Country,
    QuizLead, Tour, TourDate,
)


class ConcurrentIntegrityTests(TransactionTestCase):
    """Тесты на состояние гонки и целостность данных при параллельных запросах"""
    reset_sequences = True

    def setUp(self):
        self.country = Country.objects.create(country_name="Кыргызстан")
        self.city = City.objects.create(country=self.country, city_name="Бишкек")
        self.tour = Tour.objects.create(
            title="Concurrent Tour", tour_type="group", country=self.country, city=self.city,
            duration_days=3, price=100, currency="USD", description="T", included="T", is_active=True,
        )
        self.tour_date = TourDate.objects.create(
            tour=self.tour, start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=13), available_spots=5,
        )

    def _create_booking(self, contact, adults):
        close_old_connections()
        try:
            tour = Tour.objects.get(pk=self.tour.pk)
            tour_date = TourDate.objects.get(pk=self.tour_date.pk)
            data = {
                "tour": tour, "tour_date": tour_date, "customer_name": "C",
                "customer_contact": contact, "adults": adults, "children": 0, "comment": "",
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
            "customer_name": "Q", "customer_contact": "@c", "answers_data": {"R": "K"},
        }))
        self.assertEqual(QuizLead.objects.count(), 1)
        self.assertEqual(sorted(duplicate for _, duplicate in results), [False, True])

    def test_concurrent_contact_requests_create_one_row(self):
        results = self._run_concurrently(lambda: create_contact_request_service({
            "name": "C", "phone_or_email": "c@e.com", "subject": "Q", "message": "M", "source": "p",
        }))
        self.assertEqual(ContactRequest.objects.count(), 1)
        self.assertEqual(sorted(duplicate for _, duplicate in results), [False, True])

    def test_concurrent_confirmations_cannot_overbook(self):
        b1_id, _ = self._create_booking("+996700000001", 3)
        b2_id, _ = self._create_booking("+996700000002", 3)
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
            outcomes = list(executor.map(confirm, [b1_id, b2_id]))

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