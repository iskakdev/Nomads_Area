from django.utils.translation import get_language
from rest_framework import serializers


def is_english():
    return (get_language() or "ru").startswith("en")

def get_request_language(context=None):
    request = (context or {}).get("request")
    if request:
        parts = request.path_info.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "api":
            return parts[1].split("-")[0]

    return (get_language() or "ru").split("-")[0]

def localized_value(obj, field, lang="ru", default_lang="ru"):
    for code in [lang, "en", default_lang]:
        value = getattr(obj, f"{field}_{code}", None)
        if value:
            return value

    return getattr(obj, field, "")

class LocalizedModelSerializer(serializers.ModelSerializer):
    localized_fields = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = get_request_language(self.context)

        for field in self.localized_fields:
            if field in data:
                data[field] = localized_value(instance, field, lang)

        return data

def _file_url(instance, field, request=None):
    f = getattr(instance, field, None)
    return request.build_absolute_uri(f.url) if f and request else f.url if f else None

def _disp(val, en_map, ru_map):
    return en_map.get(val, val) if is_english() else ru_map.get(val, val)

def get_tour_type_display(v):
    return _disp(v, {"group": "Group", "private": "Private"}, {"group": "Групповой", "private": "Приватный"})

def get_season_display(v):
    return _disp(v, {"all_year": "All year", "warm": "Warm", "winter": "Winter"}, {"all_year": "Круглый год", "warm": "Тёплый", "winter": "Зима"})
