from modeltranslation.translator import TranslationOptions, register

from .models import (Attraction, City, Country, ExtraService, FAQ, ItineraryDay,
                     QuizAnswerOption, QuizQuestion, SiteSettings, TeamMember, Tour,
                     TourCategory, TourRoutePoint, TransferRoute)


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = ("about_text",)


@register(TeamMember)
class TeamMemberTranslationOptions(TranslationOptions):
    fields = ("full_name", "position", "description")


@register(Country)
class CountryTranslationOptions(TranslationOptions):
    fields = ("country_name", "hero_description")


@register(City)
class CityTranslationOptions(TranslationOptions):
    fields = ("city_name",)


@register(TourCategory)
class TourCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Tour)
class TourTranslationOptions(TranslationOptions):
    fields = ("title", "description", "included", "not_included")


@register(ItineraryDay)
class ItineraryDayTranslationOptions(TranslationOptions):
    fields = ("title", "description", "altitude", "walking_distance", "driving_distance", "accommodation")


@register(ExtraService)
class ExtraServiceTranslationOptions(TranslationOptions):
    fields = ("title", "description", "price_label")


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ("question", "answer")


@register(TourRoutePoint)
class TourRoutePointTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(Attraction)
class AttractionTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(TransferRoute)
class TransferRouteTranslationOptions(TranslationOptions):
    fields = ("departure_point", "arrival_point")


@register(QuizQuestion)
class QuizQuestionTranslationOptions(TranslationOptions):
    fields = ("text",)


@register(QuizAnswerOption)
class QuizAnswerOptionTranslationOptions(TranslationOptions):
    fields = ("text",)
