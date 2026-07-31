from django.db import models


class MarketPriceSnapshot(models.Model):
    class DemandLevel(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'

    fish_name = models.CharField(max_length=80)
    division = models.CharField(max_length=80)
    recorded_date = models.DateField()
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    demand_level = models.CharField(
        max_length=12,
        choices=DemandLevel.choices,
        default=DemandLevel.MEDIUM,
    )
    source = models.CharField(max_length=80, default='Generated sample')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recorded_date', 'division', 'fish_name']
        constraints = [
            models.UniqueConstraint(
                fields=['fish_name', 'division', 'recorded_date'],
                name='unique_market_price_snapshot',
            ),
        ]
        indexes = [
            models.Index(fields=['division', 'fish_name', '-recorded_date']),
            models.Index(fields=['recorded_date']),
        ]

    def __str__(self):
        return f'{self.fish_name} in {self.division} - {self.price_per_kg} on {self.recorded_date}'
