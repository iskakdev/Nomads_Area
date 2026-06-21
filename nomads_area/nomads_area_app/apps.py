from django.apps import AppConfig


class NomadsAreaAppConfig(AppConfig):
    name = "nomads_area_app"

    def ready(self):
        import nomads_area_app.signals  # noqa: F401
