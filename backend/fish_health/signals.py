from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import HealthRecord
from .services.core.alerts import create_health_notifications


@receiver(post_save, sender=HealthRecord)
def notify_after_health_record(sender, instance, **kwargs):
    create_health_notifications(instance)
