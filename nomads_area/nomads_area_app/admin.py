import json
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from modeltranslation.admin import TranslationAdmin
from .models import (Attraction, AttractionImage, Booking, City, ContactRequest, Country,
                     ExtraService, FAQ, ItineraryDay, Payment, QuizAnswerOption, QuizLead,
                     QuizProgress, QuizQuestion, SiteSettings, TeamMember, Tour,
                     TourCategory, TourDate, TourImage, TourPriceTier, TourRoutePoint,
                     TransferRoute, TransportRequest, VehicleType)

admin.site.site_header = "Nomads Area Admin"
admin.site.site_title = "Nomads Area"
admin.site.index_title = "Панель"


class TranslationMediaMixin:
    class Media:
        js = ("https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
              "https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js",
              "modeltranslation/js/tabbed_translation_fields.js")
        css = {"screen": ("modeltranslation/css/tabbed_translation_fields.css",)}


class TourImageInline(admin.TabularInline):
    model = TourImage; extra = 1; fields = ["image", "alt_text", "order"]

class ItineraryDayInline(admin.StackedInline):
    model = ItineraryDay; extra = 1

class TourDateInline(admin.TabularInline):
    model = TourDate; extra = 1

class TourRoutePointInline(admin.TabularInline):
    model = TourRoutePoint; extra = 1

class AttractionImageInline(admin.TabularInline):
    model = AttractionImage; extra = 1; fields = ["image", "alt_text", "order"]

class QuizAnswerOptionInline(admin.TabularInline):
    model = QuizAnswerOption; fk_name = "question"; extra = 1


class TourPriceTierFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        tiers = [f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE", False)]
        for i, t1 in enumerate(tiers):
            for j, t2 in enumerate(tiers):
                if i == j: continue
                m1, m2 = t1.get("min_people"), t2.get("min_people")
                if m1 is None or m2 is None: continue
                mx1, mx2 = t1.get("max_people") or 999999, t2.get("max_people") or 999999
                if max(m1, m2) <= min(mx1, mx2):
                    raise ValidationError("Диапазоны пересекаются")

class TourPriceTierInline(admin.TabularInline):
    model = TourPriceTier; formset = TourPriceTierFormSet; extra = 1


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["phone", "email", "years_experience", "tourists_count", "reviews_enabled"]
    fieldsets = (
        ("Контакты", {"fields": ("phone", "whatsapp", "email", "instagram_url", "facebook_url", "youtube_url", "tiktok_url", "tripadvisor_url")}),
        ("О компании", {"fields": ("about_text", "about_video_url", "years_experience", "tourists_count", "routes_count", "privacy_policy")}),
        ("Виджеты отзывов", {"fields": ("reviews_enabled", "elfsight_google_reviews_app_id",),
                             "description": "Google Reviews -- через платный Elfsight (App ID)."}),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["full_name", "position", "is_active", "order"]
    list_filter = ["is_active"]; search_fields = ["full_name", "position"]; list_editable = ["is_active", "order"]


@admin.register(Country)
class CountryAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["country_name"]; search_fields = ["country_name"]


@admin.register(City)
class CityAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["city_name", "country"]; list_filter = ["country"]
    search_fields = ["city_name", "country__country_name"]; list_select_related = ["country"]


@admin.register(TourCategory)
class TourCategoryAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["name", "is_active", "order"]; list_filter = ["is_active"]
    search_fields = ["name"]; list_editable = ["is_active", "order"]


@admin.register(Tour)
class TourAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["title", "tour_type", "price", "currency", "is_active", "created_at"]
    list_filter = ["tour_type", "season", "difficulty", "is_active", "country", "city", "categories"]
    search_fields = ["title", "description", "country__country_name", "city__city_name"]
    list_editable = ["is_active"]; filter_horizontal = ["categories"]; list_select_related = ["country", "city"]
    inlines = [TourImageInline, TourRoutePointInline, ItineraryDayInline, TourDateInline, TourPriceTierInline]


@admin.register(TourDate)
class TourDateAdmin(admin.ModelAdmin):
    list_display = ["tour", "start_date", "end_date", "available_spots"]
    list_filter = ["start_date", "end_date"]; list_select_related = ["tour"]; search_fields = ["tour__title"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "tour", "tour_date", "customer_name", "customer_contact", "status", "number_of_people", "total_price", "prepayment_amount", "created_at"]
    list_filter = ["status", "created_at", "tour__tour_type"]
    search_fields = ["customer_name", "customer_contact", "comment", "tour__title"]
    readonly_fields = ["created_at", "confirmed_at", "cancelled_at", "price_per_person", "total_price", "prepayment_amount", "currency"]
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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "booking", "provider", "amount", "currency", "status", "provider_payment_id", "created_at"]
    list_filter = ["provider", "status", "currency", "created_at"]
    search_fields = ["booking__id", "booking__customer_name", "provider_payment_id"]
    readonly_fields = ["created_at", "updated_at", "paid_at", "failed_at", "provider_payload"]
    list_select_related = ["booking"]; actions = ["mark_paid_manual"]

    def mark_paid_manual(self, request, qs):
        c = 0
        for p in qs:
            try: p.mark_paid_and_confirm_booking(provider_payload={"source": "admin"}); c += 1
            except Exception as e: self.message_user(request, f"Платёж #{p.id}: {e}", level=messages.ERROR)
        self.message_user(request, f"Подтверждено: {c}", level=messages.SUCCESS)
    mark_paid_manual.short_description = "Подтвердить вручную"


@admin.register(QuizQuestion)
class QuizQuestionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["id", "question_text", "question_type", "is_active", "order"]
    list_filter = ["question_type", "is_active"]; search_fields = ["question_text"]
    list_editable = ["is_active", "order"]; inlines = [QuizAnswerOptionInline]


@admin.register(QuizLead)
class QuizLeadAdmin(admin.ModelAdmin):
    list_display = ["id", "customer_name", "customer_contact", "status", "created_at"]
    list_filter = ["status", "created_at"]; search_fields = ["customer_name", "customer_contact"]
    list_editable = ["status"]; readonly_fields = ["created_at", "answers_data_pretty"]
    fields = ["customer_name", "customer_contact", "status", "answers_data_pretty", "created_at"]

    def answers_data_pretty(self, i):
        return json.dumps(i.answers_data, ensure_ascii=False, indent=4) if i.answers_data else "-"
    answers_data_pretty.short_description = "Ответы"


@admin.register(QuizProgress)
class QuizProgressAdmin(admin.ModelAdmin):
    list_display = ["session_key", "current_question_index", "is_completed", "created_at", "updated_at"]
    readonly_fields = ["session_key", "answers_data", "current_question_index", "is_completed", "created_at", "updated_at"]

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(FAQ)
class FAQAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["question", "tour", "is_active", "order"]; list_filter = ["is_active", "tour"]
    search_fields = ["question", "answer", "tour__title"]; list_editable = ["is_active", "order"]
    list_select_related = ["tour"]


@admin.register(ExtraService)
class ExtraServiceAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["title", "tour", "price", "currency", "is_active"]; list_filter = ["is_active", "currency", "tour"]
    search_fields = ["title", "description", "tour__title"]; list_editable = ["is_active"]
    list_select_related = ["tour"]


@admin.register(Attraction)
class AttractionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["name", "city", "is_active"]; list_filter = ["is_active", "city"]
    search_fields = ["name", "description", "city__city_name"]; list_editable = ["is_active"]
    list_select_related = ["city"]; filter_horizontal = ["tours"]; inlines = [AttractionImageInline]


@admin.register(TransferRoute)
class TransferRouteAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["departure_point", "arrival_point"]
    search_fields = ["departure_point", "arrival_point"]


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ["route", "category", "price", "seats", "bags"]; list_filter = ["category"]
    list_select_related = ["route"]; search_fields = ["route__departure_point", "route__arrival_point"]


@admin.register(TransportRequest)
class TransportRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "vehicle", "customer_name", "customer_phone", "status", "total_price", "created_at"]
    list_filter = ["status", "created_at"]; search_fields = ["customer_name", "customer_phone", "comment"]
    list_editable = ["status"]; readonly_fields = ["created_at"]; list_select_related = ["vehicle", "vehicle__route"]


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "phone_or_email", "subject", "source", "status", "created_at"]
    list_filter = ["status", "source", "created_at"]; search_fields = ["name", "phone_or_email", "message", "subject"]
    list_editable = ["status"]; readonly_fields = ["created_at"]
