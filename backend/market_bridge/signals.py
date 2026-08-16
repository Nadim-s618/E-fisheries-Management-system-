from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MarketOrder
from .services import notify_new_market_order


@receiver(post_save, sender=MarketOrder)
def notify_seller_when_market_order_is_created(sender, instance, created, **kwargs):
    if created:
        notify_new_market_order(instance)
