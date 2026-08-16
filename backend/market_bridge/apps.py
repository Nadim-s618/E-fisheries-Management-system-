from django.apps import AppConfig


class MarketBridgeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'market_bridge'
    verbose_name = 'Market Bridge'

    def ready(self):
        from . import signals  # noqa: F401
