from django.utils import translation


SUPPORTED_LANGUAGES = {"ru", "en"}
DEFAULT_LANGUAGE = "ru"


class URLLanguageMiddleware:
    """Activate language from API URL prefix."""

    API_PREFIX_INDEX = 0
    LANGUAGE_INDEX = 1

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = self._extract_language_from_path(request.path)

        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)

        translation.deactivate()

        return response

    def _extract_language_from_path(self, path):
        path_parts = path.strip("/").split("/")

        if len(path_parts) <= self.LANGUAGE_INDEX:
            return DEFAULT_LANGUAGE

        if path_parts[self.API_PREFIX_INDEX] != "api":
            return DEFAULT_LANGUAGE

        language = path_parts[self.LANGUAGE_INDEX]

        if language not in SUPPORTED_LANGUAGES:
            return DEFAULT_LANGUAGE

        return language