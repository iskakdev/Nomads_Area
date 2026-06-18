from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("nomads_area_app", "0009_request_fingerprints"),
    ]

    operations = [
        migrations.DeleteModel(name="TransportRequest"),
        migrations.DeleteModel(name="VehicleType"),
        migrations.DeleteModel(name="TransferRoute"),
    ]
