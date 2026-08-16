from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import WaterQualityReading
from .services.notification_service import create_water_quality_notifications


@receiver(post_save, sender=WaterQualityReading)
def notify_after_water_quality_reading(sender, instance, created, **kwargs):
    if created:
        create_water_quality_notifications(instance)
