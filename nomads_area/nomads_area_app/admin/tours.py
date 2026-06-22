from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from modeltranslation.admin import TranslationAdmin

from ..models import Attraction, Tour, TourDate
from .common import TranslationMediaMixin
from .inlines import (
    AttractionImageInline,
    ItineraryDayInline,
    TourAttractionInline,
    TourDateInline,
    TourImageInline,
    TourPriceTierInline,
    TourRoutePointInline,
)


class AttractionAdminForm(forms.ModelForm):
    class Meta:
        model = Attraction
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get("city")
        name = (cleaned_data.get("name") or "").strip()

        if city and name:
            duplicates = Attraction.objects.filter(city=city, name__iexact=name)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise ValidationError(
                    "Такая достопримечательность уже есть в этом городе. "
                    "Откройте существующую запись и добавьте к ней нужные туры."
                )

        return cleaned_data

@admin.register(Tour)
class TourAdmin(TranslationMediaMixin, TranslationAdmin):
    list_display = ["title", "tour_type", "price", "currency", "is_active", "created_at"]
    list_filter = ["tour_type", "season", "difficulty", "is_active", "country", "city", "categories"]
    search_fields = ["title", "description", "country__country_name", "city__city_name"]
    list_editable = ["is_active"]; filter_horizontal = ["categories"]; list_select_related = ["country", "city"]
    inlines = [TourImageInline, TourRoutePointInline, ItineraryDayInline, TourDateInline, TourPriceTierInline, TourAttractionInline]

@admin.register(TourDate)
class TourDateAdmin(admin.ModelAdmin):
    list_display = ["tour", "start_date", "end_date", "available_spots"]
    list_filter = ["start_date", "end_date"]; list_select_related = ["tour"]; search_fields = ["tour__title"]

@admin.register(Attraction)
class AttractionAdmin(TranslationMediaMixin, TranslationAdmin):
    form = AttractionAdminForm
    list_display = ["name", "city", "tours_list", "is_active"]; list_filter = ["is_active", "city", "tours"]
    search_fields = ["name", "description", "city__city_name", "tours__title"]; list_editable = ["is_active"]
    list_select_related = ["city"]; exclude = ["tours"]; inlines = [AttractionImageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tours")

    def tours_list(self, obj):
        titles = list(obj.tours.values_list("title", flat=True)[:5])
        label = ", ".join(titles) if titles else "-"
        if obj.tours.count() > 5:
            label += " ..."
        return label
    tours_list.short_description = "Туры"
