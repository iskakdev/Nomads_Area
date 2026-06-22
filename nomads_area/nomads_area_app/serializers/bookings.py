from datetime import date

from rest_framework import serializers

from ..models import Booking, ContactRequest, ExtraService, Tour
from ..services import create_booking_service, create_contact_request_service
from .common import LocalizedModelSerializer


class BookingCreateSerializer(LocalizedModelSerializer):
    number_of_people = serializers.SerializerMethodField()
    price_per_person = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    extra_services = serializers.PrimaryKeyRelatedField(queryset=ExtraService.objects.filter(is_active=True), many=True, required=False)

    class Meta:
        model = Booking
        fields = ["id", "tour", "tour_date", "preferred_start_date", "preferred_end_date",
                  "customer_name", "customer_contact", "adults", "children", "comment",
                  "extra_services", "number_of_people", "price_per_person", "total_price",
                  "currency", "status", "created_at"]
        read_only_fields = ["id", "number_of_people", "price_per_person", "total_price",
                            "currency", "status", "created_at"]

    def validate(self, attrs):
        tour = attrs["tour"]

        if not tour.is_active:
            raise serializers.ValidationError({
                "tour": "Этот тур сейчас недоступен для бронирования"
            })

        tour_date = attrs.get("tour_date")
        total = attrs["adults"] + attrs.get("children", 0)
        self._price_tier = self._resolved_date = None

        if total <= 0:
            raise serializers.ValidationError({"non_field_errors": "Количество людей > 0"})

        if tour.tour_type == Tour.TOUR_TYPE_GROUP:
            if not tour_date:
                raise serializers.ValidationError({"tour_date": "Выберите дату"})
            if tour_date.tour_id != tour.id:
                raise serializers.ValidationError({"tour_date": "Не та дата"})
            if tour_date.start_date < date.today():
                raise serializers.ValidationError({"tour_date": "Дата в прошлом"})
            if total > tour_date.available_spots:
                raise serializers.ValidationError({"non_field_errors": f"Мест: {tour_date.available_spots}"})
            self._resolved_date = tour_date

        elif tour.tour_type == Tour.TOUR_TYPE_PRIVATE:
            if tour_date:
                raise serializers.ValidationError({"tour_date": "Приватный без фикс. даты"})
            s, e = attrs.get("preferred_start_date"), attrs.get("preferred_end_date")
            if not s or not e:
                raise serializers.ValidationError({"preferred_start_date": "Укажите диапазон"})
            if s < date.today() or s > e:
                raise serializers.ValidationError({"preferred_end_date": "Некорректные даты"})
            tier = tour.price_tiers.filter(min_people__lte=total, max_people__gte=total).first() or \
                   tour.price_tiers.filter(min_people__lte=total, max_people__isnull=True).first()
            if not tier:
                raise serializers.ValidationError({"non_field_errors": f"Нет тарифа для {total} чел"})
            self._price_tier = tier

        extra_services = attrs.get("extra_services") or []
        invalid_services = [service.id for service in extra_services if service.tour_id != tour.id]
        if invalid_services:
            raise serializers.ValidationError({"extra_services": "Услуга не относится к выбранному туру"})

        return attrs

    def create(self, validated_data):
        b, is_dup = create_booking_service(
            validated_data,
            price_tier=self._price_tier,
            tour_date=self._resolved_date,
        )
        self.is_duplicate = is_dup
        return b

    def get_number_of_people(self, obj): return obj.number_of_people
    def get_price_per_person(self, obj): return obj.price_per_person
    def get_total_price(self, obj): return obj.total_price

class ContactRequestSerializer(LocalizedModelSerializer):
    class Meta:
        model = ContactRequest
        fields = ["id", "subject", "name", "phone_or_email", "message", "source", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def create(self, validated_data):
        i, is_dup = create_contact_request_service(validated_data)
        self.is_duplicate = is_dup
        return i
