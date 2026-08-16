from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import WeatherReport
from .services.notification_service import create_weather_notifications


@receiver(post_save, sender=WeatherReport)
def notify_after_weather_report(sender, instance, **kwargs):
    create_weather_notifications(instance)
