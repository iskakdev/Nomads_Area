from django.contrib import admin, messages

from ..models import Booking, ContactRequest


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "tour", "tour_date", "customer_name", "customer_contact", "status", "number_of_people", "total_price", "created_at"]
    list_display_links = ["id", "tour"]
    list_editable = ["status"]
    list_filter = ["status", "created_at", "tour__tour_type"]
    search_fields = ["customer_name", "customer_contact", "comment", "tour__title"]
    readonly_fields = ["created_at", "confirmed_at", "cancelled_at", "price_per_person", "total_price", "currency"]
    list_select_related = ["tour", "tour_date"]; actions = ["confirm_selected_bookings", "cancel_selected_bookings"]

    def confirm_selected_bookings(self, request, qs):
        c = 0
        for b in qs:
            try: b.confirm_and_reserve(); c += 1
            except Exception as e: self.message_user(request, f"Бронь #{b.id}: {e}", level=messages.ERROR)
        self.message_user(request, f"Подтверждено: {c}", level=messages.SUCCESS)
    confirm_selected_bookings.short_description = "Подтвердить и зарезервировать"

    def cancel_selected_bookings(self, request, qs):
        c = 0
        for b in qs:
            try: b.cancel(); c += 1
            except Exception as e: self.message_user(request, f"Бронь #{b.id}: {e}", level=messages.ERROR)
        self.message_user(request, f"Отменено: {c}", level=messages.SUCCESS)
    cancel_selected_bookings.short_description = "Отменить выбранные"

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "phone_or_email", "subject", "source", "status", "created_at"]
    list_filter = ["status", "source", "created_at"]; search_fields = ["name", "phone_or_email", "message", "subject"]
    list_editable = ["status"]; readonly_fields = ["created_at"]
