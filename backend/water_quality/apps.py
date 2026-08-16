from django.apps import AppConfig


class WaterQualityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'water_quality'
    verbose_name = 'Water Quality'

    def ready(self):
        from . import signals  # noqa: F401
