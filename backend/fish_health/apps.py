from django.apps import AppConfig


class FishHealthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fish_health'

    def ready(self):
        from . import signals  # noqa: F401
