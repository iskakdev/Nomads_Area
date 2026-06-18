from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nomads_area_app", "0008_localize_extra_service_features"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="request_fingerprint",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="contactrequest",
            name="request_fingerprint",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="quizlead",
            name="request_fingerprint",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=64),
        ),
        migrations.AddField(
            model_name="transportrequest",
            name="bags",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="Багаж"),
        ),
        migrations.AddField(
            model_name="transportrequest",
            name="passengers",
            field=models.PositiveSmallIntegerField(default=1, verbose_name="Пассажиры"),
        ),
        migrations.AddField(
            model_name="transportrequest",
            name="request_fingerprint",
            field=models.CharField(blank=True, db_index=True, editable=False, max_length=64),
        ),
    ]
