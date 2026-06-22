from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from ..models import (
    Attraction,
    AttractionImage,
    ItineraryDay,
    QuizAnswerOption,
    TourDate,
    TourImage,
    TourPriceTier,
    TourRoutePoint,
)


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

class TourAttractionInline(admin.TabularInline):
    model = Attraction.tours.through
    extra = 0
    verbose_name = "Достопримечательность"
    verbose_name_plural = "Достопримечательности"
