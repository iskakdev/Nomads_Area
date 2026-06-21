# Generated manually to sync itinerary tags column.
#
# Production already had this column when the migration was introduced, but a
# fresh test database does not. Keep the database operation idempotent so both
# cases work.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomads_area_app', '0018_remove_tourcategory_description_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE nomads_area_app_itineraryday "
                        "ADD COLUMN IF NOT EXISTS tags varchar(255);"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="UPDATE nomads_area_app_itineraryday SET tags = '' WHERE tags IS NULL;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags SET DEFAULT '';",
                    reverse_sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags DROP DEFAULT;",
                ),
                migrations.RunSQL(
                    sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags SET NOT NULL;",
                    reverse_sql="ALTER TABLE nomads_area_app_itineraryday ALTER COLUMN tags DROP NOT NULL;",
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
