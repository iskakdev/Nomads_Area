import json
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from modeltranslation.admin import TranslationAdmin

from .models import (FAQ, Payment, Attraction, AttractionImage, Booking, City, ContactRequest, Country,
                     ExtraService, ItineraryDay, QuizAnswerOption, QuizLead, QuizProgress,
                     QuizQuestion, SiteSettings, TeamMember, Tour, TourCategory, TourDate,
                     TourImage, TourPriceTier, TourRoutePoint, TransferRoute, TransportRequest,
                     VehicleType)


admin.site.site_header = "Nomads Area Admin"
admin.site.site_title = "Nomads Area"
admin.site.index_title = "Панель управления"


class TranslationMediaMixin:
    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
            "https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js",
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
        count = sum(1 for form in self.forms if form.cleaned_data and not form.cleaned_data.get("DELETE", False))

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
    list_display = ["phone", "email", "instagram_url", "whatsapp", "years_experience", "tourists_count"]
    fieldsets = (
        ("Контакты", {"fields": ("phone", "whatsapp", "email")}),
        ("Социальные сети", {"fields": ("instagram_url", "facebook_url", "youtube_url", "tiktok_url", "tripadvisor_url")}),
        ("О компании", {"fields": ("about_text", "about_video_url")}),
        ("Цифры на сайте", {"fields": ("years_experience", "tourists_count", "routes_count")}),
        ("Документы", {"fields": ("privacy_policy_url",)})
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(Country)
class CountryAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["country_name", "hero_description"]
    search_fields = ["country_name"]
    fieldsets = (
        ("Основная информация", {"fields": ("country_name", "hero_description")}),
        ("Изображения", {"fields": ("country_image", "symbol_image")})
    )


@admin.register(City)
class CityAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["city_name", "country"]
    list_filter = ["country"]
    list_select_related = ["country"]
    search_fields = ["city_name", "country__country_name"]
    fieldsets = (
        ("Основная информация", {"fields": ("country", "city_name")}),
        ("Изображение", {"fields": ("city_image",)})
    )


@admin.register(TourCategory)
class TourCategoryAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["name", "icon"]
    search_fields = ["name"]


@admin.register(Tour)
class TourAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["title", "tour_type", "country", "city", "price", "currency", "is_active", "created_at"]
    list_filter = ["tour_type", "season", "difficulty", "country", "is_active"]
    list_select_related = ["country", "city"]
    search_fields = ["title", "description", "country__country_name", "city__city_name"]
    filter_horizontal = ["categories"]
    readonly_fields = ["created_at"]
    inlines = [
        TourImageInline, ItineraryDayInline, TourDateInline, TourPriceTierInline, ExtraServiceInline, FAQInline,
        TourRoutePointInline,
    ]
    fieldsets = (
        ("Основная информация", {"fields": ("title", "tour_type", "is_active")}),
        ("Локация", {"fields": ("country", "city", "categories")}),
        ("Параметры тура", {"fields": ("season", "duration_days", "difficulty", "max_people")}),
        ("Цена", {"fields": ("price", "currency")}),
        ("Описание", {"fields": ("description", "included", "not_included", "activity_tags")}),
        ("Ссылки", {"fields": ("tripadvisor_url",)}),
        ("Служебная информация", {"fields": ("created_at",)})
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["customer_name", "tour", "tour_date", "number_of_people", "total_price", "status", "created_at"]
    list_filter = ["status", "tour__tour_type", "created_at"]
    list_select_related = ["tour", "tour_date"]
    search_fields = ["customer_name", "customer_contact", "tour__title"]
    list_editable = ["status"]
    readonly_fields = ["price_per_person", "total_price", "created_at"]
    fieldsets = (
        ("Клиент", {"fields": ("customer_name", "customer_contact", "people_details", "comment")}),
        ("Тур", {"fields": ("tour", "tour_date", "preferred_start_date", "preferred_end_date")}),
        ("Количество людей", {"fields": ("adults", "children", "number_of_people")}),
        ("Стоимость", {"fields": ("price_per_person", "total_price")}),
        ("Статус", {"fields": ("status",)}),
        ("Служебная информация", {"fields": ("created_at",)})
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["booking", "provider", "amount", "currency", "status", "created_at", "paid_at"]
    list_editable = ["status"]
    list_filter = ["provider", "status", "currency", "created_at"]
    list_select_related = ["booking", "booking__tour"]
    search_fields = ["booking__customer_name", "booking__customer_contact", "external_payment_id"]
    readonly_fields = ["booking", "provider", "amount", "currency", "external_payment_id", "payment_url", "created_at", "paid_at"]
    fieldsets = (
        ("Бронирование", {"fields": ("booking",)}),
        ("Платёж", {"fields": ("provider", "amount", "currency", "status")}),
        ("FinikPay", {"fields": ("external_payment_id", "payment_url")}),
        ("Даты", {"fields": ("created_at", "paid_at")})
    )


@admin.register(Attraction)
class AttractionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["name", "city", "is_active"]
    list_filter = ["city", "city__country", "is_active"]
    list_select_related = ["city", "city__country"]
    search_fields = ["name", "description", "city__city_name"]
    filter_horizontal = ["tours"]
    inlines = [AttractionImageInline]
    fieldsets = (
        ("Основная информация", {"fields": ("city", "name", "description", "is_active")}),
        ("Связанные туры", {"fields": ("tours",)}),
        ("Главное изображение", {"fields": ("image",)})
    )


@admin.register(TransferRoute)
class TransferRouteAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["departure_point", "arrival_point", "distance_km"]
    search_fields = ["departure_point", "arrival_point"]
    inlines = [VehicleTypeInline]


@admin.register(TransportRequest)
class TransportRequestAdmin(admin.ModelAdmin):
    list_display = ["customer_phone", "vehicle", "travel_date", "passengers", "total_price", "status", "created_at"]
    list_filter = ["status", "travel_date", "created_at"]
    list_select_related = ["vehicle", "vehicle__route"]
    list_editable = ["status"]
    search_fields = ["customer_name", "customer_phone", "flight_number"]
    readonly_fields = ["total_price", "created_at"]


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone_or_email", "subject", "source", "status", "created_at"]
    list_filter = ["status", "source", "created_at"]
    list_editable = ["status"]
    search_fields = ["name", "phone_or_email", "subject", "message"]
    readonly_fields = ["created_at"]


@admin.register(TeamMember)
class TeamMemberAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["full_name", "position", "order", "is_active"]
    list_filter = ["is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["full_name", "position"]
    fieldsets = (
        ("Основная информация", {"fields": ("full_name", "position", "description")}),
        ("Фото и порядок", {"fields": ("photo", "order", "is_active")})
    )


@admin.register(QuizQuestion)
class QuizQuestionAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["text", "question_type", "order", "is_active"]
    list_filter = ["question_type", "is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["text"]
    inlines = [QuizAnswerOptionInline]


@admin.register(QuizLead)
class QuizLeadAdmin(admin.ModelAdmin):
    list_display = ["name", "phone_or_telegram", "is_processed", "created_at"]
    list_filter = ["is_processed", "created_at"]
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
    readonly_fields = ["session_key", "answers", "current_question_index", "is_completed", "created_at", "updated_at"]

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(FAQ)
class FAQAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["question", "tour", "is_active", "order"]
    list_filter = ["is_active", "tour"]
    search_fields = ["question", "answer", "tour__title"]
    list_editable = ["is_active", "order"]


@admin.register(ExtraService)
class ExtraServiceAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["title", "tour", "price", "currency", "is_active"]
    list_filter = ["is_active", "currency", "tour"]
    search_fields = ["title", "description", "tour__title"]
    list_editable = ["is_active"]


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ["route", "category", "price", "seats", "bags"]
    list_filter = ["category"]
    list_select_related = ["route"]
    search_fields = ["route__departure_point", "route__arrival_point"]


@admin.register(TourDate)
class TourDateAdmin(admin.ModelAdmin):
    list_display = ["tour", "start_date", "end_date", "available_spots"]
    list_filter = ["start_date", "end_date"]
    list_select_related = ["tour"]
    search_fields = ["tour__title"]


@admin.register(TourPriceTier)
class TourPriceTierAdmin(admin.ModelAdmin):
    list_display = ["tour", "min_people", "max_people", "price_per_person"]
    list_select_related = ["tour"]
    search_fields = ["tour__title"]
