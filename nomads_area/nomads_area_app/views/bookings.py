from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import AllowAny

from ..notifications import send_booking_notification, send_contact_notification
from ..serializers import BookingCreateSerializer, ContactRequestSerializer
from ..throttles import FormSubmitThrottle


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        booking = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_booking_notification(booking))


class ContactRequestCreateView(generics.CreateAPIView):
    serializer_class = ContactRequestSerializer
    permission_classes = [AllowAny]
    throttle_classes = [FormSubmitThrottle]

    def perform_create(self, serializer):
        instance = serializer.save()
        if not getattr(serializer, "is_duplicate", False):
            transaction.on_commit(lambda: send_contact_notification(instance))
