import json

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from modeltranslation.admin import TranslationAdmin

from .models import (FAQ, Attraction, AttractionImage, Booking, City, ContactRequest,
                     Country, ExtraService, ItineraryDay, QuizAnswerOption, QuizLead,
                     QuizProgress, QuizQuestion, SiteSettings, TeamMember, Tour,
                     TourCategory, TourDate, TourImage, TourPriceTier, TourRoutePoint,
                     TransferRoute, TransportRequest, VehicleType)


class TranslationMediaMixin:
    class Media:
        js = (
            "http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
            "http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js",
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {
            "screen": ("modeltranslation/css/tabbed_translation_fields.css",),
        }


class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1


class ItineraryDayInline(admin.StackedInline):
    model = ItineraryDay
    extra = 1


class TourDateInline(admin.TabularInline):
    model = TourDate
    extra = 1


class TourPriceTierInline(admin.TabularInline):
    model = TourPriceTier
    extra = 1


class ExtraServiceInline(admin.StackedInline):
    model = ExtraService
    extra = 0


class FAQInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = sum(
            1 for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        )
        if count > FAQ.MAX_FAQ_PER_TOUR:
            raise ValidationError(f"Максимум {FAQ.MAX_FAQ_PER_TOUR} FAQ для одного тура.")


class FAQInline(admin.StackedInline):
    model = FAQ
    extra = 0
    formset = FAQInlineFormSet


class TourRoutePointInline(admin.TabularInline):
    model = TourRoutePoint
    extra = 0


class AttractionImageInline(admin.TabularInline):
    model = AttractionImage
    extra = 1


class QuizAnswerOptionInline(admin.TabularInline):
    model = QuizAnswerOption
    extra = 3


class VehicleTypeInline(admin.TabularInline):
    model = VehicleType
    extra = 1


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["phone", "email", "years_experience", "tourists_count"]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(Country)
class CountryAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["country_name", "hero_description"]
    search_fields = ["country_name"]


@admin.register(TeamMember)
class TeamMemberAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["full_name", "position", "order", "is_active"]
    list_filter = ["is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["full_name", "position"]


@admin.register(City)
class CityAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["city_name", "country"]
    list_filter = ["country"]
    list_select_related = ["country"]
    search_fields = ["city_name"]


@admin.register(TourCategory)
class TourCategoryAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["name"]


@admin.register(Tour)
class TourAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["title", "tour_type", "country", "city", "price", "currency", "is_active", "created_at"]
    list_filter = ["tour_type", "season", "difficulty", "country", "is_active"]
    list_select_related = ["country", "city"]
    search_fields = ["title", "description"]
    filter_horizontal = ["categories"]
    inlines = [TourImageInline, ItineraryDayInline, TourDateInline,
               TourPriceTierInline, ExtraServiceInline, FAQInline, TourRoutePointInline]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["customer_name", "tour", "tour_date", "number_of_people", "total_price", "status", "created_at"]
    list_filter = ["status", "tour__tour_type"]
    list_select_related = ["tour", "tour_date"]
    search_fields = ["customer_name", "customer_contact", "tour__title"]
    list_editable = ["status"]
    readonly_fields = ["price_per_person", "total_price", "created_at"]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["text", "question_type", "order", "is_active"]
    list_filter = ["question_type", "is_active"]
    inlines = [QuizAnswerOptionInline]


@admin.register(QuizLead)
class QuizLeadAdmin(admin.ModelAdmin):
    list_display = ["name", "phone_or_telegram", "is_processed", "created_at"]
    list_filter = ["is_processed"]
    list_editable = ["is_processed"]
    search_fields = ["name", "phone_or_telegram"]
    readonly_fields = ["answers_display", "created_at"]

    def answers_display(self, obj):
        return json.dumps(obj.answers, indent=4, ensure_ascii=False)

    answers_display.short_description = "Ответы"


@admin.register(QuizProgress)
class QuizProgressAdmin(admin.ModelAdmin):
    list_display = ["session_key", "current_question_index", "is_completed", "updated_at"]
    list_filter = ["is_completed"]


@admin.register(Attraction)
class AttractionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["name", "city", "is_active"]
    list_filter = ["city", "is_active"]
    list_select_related = ["city"]
    search_fields = ["name"]
    filter_horizontal = ["tours"]
    inlines = [AttractionImageInline]


@admin.register(TransferRoute)
class TransferRouteAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["departure_point", "arrival_point", "distance_km"]
    search_fields = ["departure_point", "arrival_point"]
    inlines = [VehicleTypeInline]


@admin.register(TransportRequest)
class TransportRequestAdmin(admin.ModelAdmin):
    list_display = ["customer_phone", "vehicle", "travel_date", "passengers", "total_price", "status", "created_at"]
    list_filter = ["status"]
    list_select_related = ["vehicle"]
    list_editable = ["status"]
    search_fields = ["customer_name", "customer_phone"]


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone_or_email", "subject", "source", "status", "created_at"]
    list_filter = ["status", "source"]
    list_editable = ["status"]
    search_fields = ["name", "phone_or_email", "subject"]
