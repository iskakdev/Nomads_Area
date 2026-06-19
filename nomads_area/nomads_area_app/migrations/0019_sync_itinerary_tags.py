# Generated manually to sync existing itinerary tags column

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomads_area_app', '0018_remove_tourcategory_description_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags SET DEFAULT '';",
                    reverse_sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags DROP DEFAULT;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags DROP NOT NULL;",
                    reverse_sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags SET NOT NULL;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="itineraryday",
                    name="tags",
                    field=models.CharField(blank=True, default="", max_length=255, verbose_name="Теги"),
                ),
            ],
        ),
    ]
