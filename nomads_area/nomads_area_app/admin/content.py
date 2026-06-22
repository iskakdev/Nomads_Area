from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from ..models import (
    City,
    Country,
    ExtraService,
    FAQ,
    SiteSettings,
    TeamMember,
    TourCategory,
)
from .common import TranslationMediaMixin


@admin.register(SiteSettings)
class SiteSettingsAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["phone", "email", "years_experience", "tourists_count", "reviews_enabled"]
    fieldsets = (
        ("Контакты", {"fields": ("phone", "whatsapp", "email", "instagram_url", "facebook_url", "youtube_url", "tiktok_url")}),
        ("О компании", {"fields": ("about_text", "about_video_url", "years_experience", "tourists_count", "routes_count", "privacy_policy")}),
        ("Виджеты отзывов", {"fields": ("reviews_enabled", "elfsight_google_reviews_app_id",),
                             "description": "Отзывы через Elfsight. Можно использовать TripAdvisor Reviews, Google Reviews или другой Elfsight Reviews widget. Вставьте App ID."}),
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
    fields = ["tour", "title", "description", "image", "price", "currency", "price_label", "is_active"]

class Admin(admin.ModelAdmin):
    list_display = (
        "order",
        "author",
        "title",
        "rating",
        "published_date",
        "is_active",
    )
    list_display_links = (
        "author",
        "title",
    )
    list_editable = (
        "rating",
        "published_date",
        "is_active",
        "order",
    )
    list_filter = (
        "is_active",
        "rating",
        "published_date",
    )
    search_fields = (
        "author",
        "title",
        "text",
        "url",
    )
    ordering = (
        "order",
        "-published_date",
        "-id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    fields = (
        "author",
        "rating",
        "published_date",
        "order",
        "is_active",
        "title",
        "text",
        "avatar_url",
        "url",
        "created_at",
        "updated_at",
    )
