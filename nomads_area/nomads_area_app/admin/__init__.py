# Import modules so @admin.register decorators are executed by Django admin autodiscover.
from .common import TranslationMediaMixin
from .tours import AttractionAdminForm
from . import content, tours, bookings, quiz

__all__ = [
    "TranslationMediaMixin",
    "AttractionAdminForm",
    "content",
    "tours",
    "bookings",
    "quiz",
]
