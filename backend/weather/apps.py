from django.apps import AppConfig


class WeatherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'weather'
    verbose_name = 'Weather'

    def ready(self):
        from . import signals  # noqa: F401
