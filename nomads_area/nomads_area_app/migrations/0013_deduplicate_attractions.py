from collections import defaultdict

from django.db import migrations


def normalize_name(value):
    return " ".join((value or "").strip().casefold().split())


def merge_duplicate_attractions(apps, schema_editor):
    Attraction = apps.get_model("nomads_area_app", "Attraction")
    AttractionImage = apps.get_model("nomads_area_app", "AttractionImage")

    groups = defaultdict(list)
    for attraction in Attraction.objects.all().order_by("city_id", "id"):
        key = (attraction.city_id, normalize_name(attraction.name))
        if key[1]:
            groups[key].append(attraction.id)

    copy_fields = [
        field.name
        for field in Attraction._meta.fields
        if field.name.startswith("name_") or field.name.startswith("description_")
    ]
    copy_fields.extend(["description", "image"])

    for attraction_ids in groups.values():
        if len(attraction_ids) < 2:
            continue

        attractions = list(Attraction.objects.filter(id__in=attraction_ids).order_by("-is_active", "id"))
        primary = attractions[0]

        for duplicate in attractions[1:]:
            primary.tours.add(*duplicate.tours.all())
            AttractionImage.objects.filter(attraction_id=duplicate.id).update(attraction_id=primary.id)

            update_fields = []
            for field_name in copy_fields:
                primary_value = getattr(primary, field_name, None)
                duplicate_value = getattr(duplicate, field_name, None)
                if not primary_value and duplicate_value:
                    setattr(primary, field_name, duplicate_value)
                    update_fields.append(field_name)

            if update_fields:
                primary.save(update_fields=update_fields)

            duplicate.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("nomads_area_app", "0012_admin_model_labels"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_attractions, migrations.RunPython.noop),
    ]
