from django.db import migrations


FEATURE_TRANSLATIONS = {
    153: {
        "ru": ["4K Ultra HD", "Рабочий диапазон 10–50 м", "Высота полёта до 300 м", "Лёгкие динамичные кадры"],
        "en": ["4K Ultra HD", "Operating range 10–50 m", "Flight altitude up to 300 m", "Lightweight dynamic shots"],
        "es": ["4K Ultra HD", "Alcance operativo de 10–50 m", "Altura de vuelo de hasta 300 m", "Tomas dinámicas y ligeras"],
        "fr": ["4K Ultra HD", "Portée de fonctionnement de 10 à 50 m", "Altitude de vol jusqu’à 300 m", "Plans dynamiques et légers"],
        "de": ["4K Ultra HD", "Arbeitsbereich 10–50 m", "Flughöhe bis zu 300 m", "Leichte dynamische Aufnahmen"],
    },
    154: {
        "ru": ["4K HDR", "Рабочий диапазон 10–100 м", "Высота полёта до 500 м", "Стабильная съёмка на ветру"],
        "en": ["4K HDR", "Operating range 10–100 m", "Flight altitude up to 500 m", "Stable filming in windy conditions"],
        "es": ["4K HDR", "Alcance operativo de 10–100 m", "Altura de vuelo de hasta 500 m", "Grabación estable con viento"],
        "fr": ["4K HDR", "Portée de fonctionnement de 10 à 100 m", "Altitude de vol jusqu’à 500 m", "Prise de vue stable par vent"],
        "de": ["4K HDR", "Arbeitsbereich 10–100 m", "Flughöhe bis zu 500 m", "Stabile Aufnahmen bei Wind"],
    },
    155: {
        "ru": ["Вертикальные видео для Reels/TikTok", "Съёмка на телефон", "Короткий монтаж", "Передача файлов после тура"],
        "en": ["Vertical videos for Reels/TikTok", "Filming with a phone", "Short video edit", "File delivery after the tour"],
        "es": ["Videos verticales para Reels/TikTok", "Grabación con teléfono", "Edición de video corta", "Entrega de archivos después del tour"],
        "fr": ["Vidéos verticales pour Reels/TikTok", "Tournage au téléphone", "Montage vidéo court", "Livraison des fichiers après le circuit"],
        "de": ["Vertikale Videos für Reels/TikTok", "Aufnahmen mit dem Smartphone", "Kurzer Videoschnitt", "Dateiübergabe nach der Tour"],
    },
    156: {
        "ru": ["Дрон + камера телефона", "Горные панорамы", "Короткие видео для соцсетей", "Лучшие точки для съёмки"],
        "en": ["Drone + phone camera", "Mountain panoramas", "Short videos for social media", "The best filming locations"],
        "es": ["Dron + cámara de teléfono", "Panorámicas de montaña", "Videos cortos para redes sociales", "Los mejores lugares para grabar"],
        "fr": ["Drone + caméra de téléphone", "Panoramas de montagne", "Courtes vidéos pour les réseaux sociaux", "Les meilleurs lieux de tournage"],
        "de": ["Drohne + Smartphone-Kamera", "Bergpanoramen", "Kurze Videos für soziale Medien", "Die besten Aufnahmeorte"],
    },
}


def populate_feature_translations(apps, schema_editor):
    ExtraService = apps.get_model("nomads_area_app", "ExtraService")

    for service_id, translations in FEATURE_TRANSLATIONS.items():
        ExtraService.objects.filter(pk=service_id).update(
            features_ru=translations["ru"],
            features_en=translations["en"],
            features_es=translations["es"],
            features_fr=translations["fr"],
            features_de=translations["de"],
        )


def clear_feature_translations(apps, schema_editor):
    ExtraService = apps.get_model("nomads_area_app", "ExtraService")
    ExtraService.objects.filter(pk__in=FEATURE_TRANSLATIONS).update(
        features_ru=[],
        features_en=[],
        features_es=[],
        features_fr=[],
        features_de=[],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("nomads_area_app", "0007_extraservice_features_de_extraservice_features_en_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_feature_translations, clear_feature_translations),
    ]
