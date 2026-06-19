from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("nomads_area_app", "0011_remove_payments"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="attractionimage",
            options={
                "ordering": ["order", "id"],
                "verbose_name": "Фото достопримечательности",
                "verbose_name_plural": "Галерея достопримечательностей",
            },
        ),
        migrations.AlterModelOptions(
            name="contactrequest",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Контактная заявка",
                "verbose_name_plural": "Контактные заявки",
            },
        ),
        migrations.AlterModelOptions(
            name="extraservice",
            options={
                "verbose_name": "Дополнительная услуга",
                "verbose_name_plural": "Дополнительные услуги",
            },
        ),
        migrations.AlterModelOptions(
            name="itineraryday",
            options={
                "ordering": ["day_number"],
                "verbose_name": "День маршрута",
                "verbose_name_plural": "Программа тура",
            },
        ),
        migrations.AlterModelOptions(
            name="quizansweroption",
            options={
                "verbose_name": "Ответ квиза",
                "verbose_name_plural": "Ответы квиза",
            },
        ),
        migrations.AlterModelOptions(
            name="quizlead",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Заявка из квиза",
                "verbose_name_plural": "Заявки из квиза",
            },
        ),
        migrations.AlterModelOptions(
            name="quizquestion",
            options={
                "ordering": ["order", "id"],
                "verbose_name": "Вопрос квиза",
                "verbose_name_plural": "Вопросы квиза",
            },
        ),
        migrations.AlterModelOptions(
            name="tourdate",
            options={
                "ordering": ["start_date"],
                "verbose_name": "Дата тура",
                "verbose_name_plural": "Даты групповых туров",
            },
        ),
        migrations.AlterModelOptions(
            name="tourimage",
            options={
                "ordering": ["order", "id"],
                "verbose_name": "Фото тура",
                "verbose_name_plural": "Фото туров",
            },
        ),
        migrations.AlterModelOptions(
            name="tourpricetier",
            options={
                "ordering": ["min_people"],
                "verbose_name": "Цена приватного тура",
                "verbose_name_plural": "Цены приватных туров",
            },
        ),
        migrations.AlterModelOptions(
            name="tourroutepoint",
            options={
                "ordering": ["order", "id"],
                "verbose_name": "Точка маршрута",
                "verbose_name_plural": "Точки маршрута",
            },
        ),
    ]
