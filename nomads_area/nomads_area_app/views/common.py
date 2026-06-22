from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


cache_public_api = method_decorator(
    cache_page(
        settings.API_CACHE_TIMEOUT,
        key_prefix=settings.API_CACHE_KEY_PREFIX,
    ),
    name="dispatch",
)
