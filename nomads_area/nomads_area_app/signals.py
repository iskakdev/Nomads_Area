import logging

from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .models import (
    Attraction,
    AttractionImage,
    City,
    Country,
    ExtraService,
    FAQ,
    ItineraryDay,
    QuizAnswerOption,
    QuizQuestion,
    SiteSettings,
    TeamMember,
    Tour,
    TourCategory,
    TourDate,
    TourImage,
    TourPriceTier,
    TourRoutePoint,
)

logger = logging.getLogger(__name__)


PUBLIC_API_CACHE_MODELS = (
    Attraction,
    AttractionImage,
    City,
    Country,
    ExtraService,
    FAQ,
    ItineraryDay,
    QuizAnswerOption,
    QuizQuestion,
    SiteSettings,
    TeamMember,
    Tour,
    TourCategory,
    TourDate,
    TourImage,
    TourPriceTier,
    TourRoutePoint,
)

PUBLIC_API_M2M_THROUGH_MODELS = (
    Tour.categories.through,
    Attraction.tours.through,
)


def clear_public_api_cache(sender=None, **kwargs):
    try:
        cache.clear()
    except Exception:
        logger.exception("Failed to clear public API cache")


for model in PUBLIC_API_CACHE_MODELS:
    post_save.connect(clear_public_api_cache, sender=model, weak=False)
    post_delete.connect(clear_public_api_cache, sender=model, weak=False)

for through_model in PUBLIC_API_M2M_THROUGH_MODELS:
    m2m_changed.connect(clear_public_api_cache, sender=through_model, weak=False)
