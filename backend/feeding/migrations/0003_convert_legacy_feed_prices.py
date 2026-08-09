from decimal import Decimal

from django.db import migrations


def convert_legacy_prices(apps, schema_editor):
    FeedingRecommendation = apps.get_model('feeding', 'FeedingRecommendation')
    legacy_price = Decimal('4.50')
    local_price = Decimal('135.00')

    for recommendation in FeedingRecommendation.objects.filter(price_per_kg=legacy_price):
        recommendation.price_per_kg = local_price
        recommendation.estimated_cost = (
            recommendation.recommended_feed_kg * local_price
        ).quantize(Decimal('0.01'))
        recommendation.save(update_fields=['price_per_kg', 'estimated_cost'])


class Migration(migrations.Migration):
    dependencies = [
        ('feeding', '0002_update_default_feed_price'),
    ]

    operations = [
        migrations.RunPython(convert_legacy_prices, migrations.RunPython.noop),
    ]
