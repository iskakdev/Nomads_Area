from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("nomads_area_app", "0010_remove_transfers"),
    ]

    operations = [
        migrations.DeleteModel(name="Payment"),
        migrations.RemoveField(
            model_name="booking",
            name="prepayment_amount",
        ),
    ]
