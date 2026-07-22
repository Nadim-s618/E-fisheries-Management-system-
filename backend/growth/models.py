from django.core.exceptions import ValidationError
from django.db import models

from stocks.models import FishStock


class GrowthRecord(models.Model):
    stock = models.ForeignKey(
        FishStock,
        on_delete=models.CASCADE,
        related_name='growth_records',
    )
    recorded_date = models.DateField()
    sample_count = models.PositiveIntegerField()
    average_weight_g = models.DecimalField(max_digits=8, decimal_places=2)
    average_length_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    mortality_count = models.PositiveIntegerField(default=0)
    feed_used_kg = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'store'
        ordering = ['stock__pond__name', 'stock__batch_name', 'recorded_date']
        constraints = [
            models.UniqueConstraint(
                fields=['stock', 'recorded_date'],
                name='unique_growth_record_date_per_stock',
            ),
            models.CheckConstraint(
                condition=models.Q(sample_count__gt=0),
                name='growth_sample_count_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(average_weight_g__gt=0),
                name='growth_average_weight_positive',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(average_length_cm__isnull=True)
                    | models.Q(average_length_cm__gt=0)
                ),
                name='growth_average_length_positive_when_set',
            ),
            models.CheckConstraint(
                condition=models.Q(mortality_count__gte=0),
                name='growth_mortality_count_not_negative',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(feed_used_kg__isnull=True)
                    | models.Q(feed_used_kg__gt=0)
                ),
                name='growth_feed_used_positive_when_set',
            ),
        ]

    def clean(self):
        errors = {}

        if self.sample_count is not None and self.sample_count <= 0:
            errors['sample_count'] = 'Sample count must be greater than zero.'

        if self.average_weight_g is not None and self.average_weight_g <= 0:
            errors['average_weight_g'] = 'Average weight must be greater than zero.'

        if self.average_length_cm is not None and self.average_length_cm <= 0:
            errors['average_length_cm'] = 'Average length must be greater than zero.'

        if self.mortality_count is not None and self.mortality_count < 0:
            errors['mortality_count'] = 'Mortality count cannot be negative.'

        if self.feed_used_kg is not None and self.feed_used_kg <= 0:
            errors['feed_used_kg'] = 'Feed used must be greater than zero.'

        if (
            self.recorded_date
            and self.stock_id
            and self.recorded_date < self.stock.stocking_date
        ):
            errors['recorded_date'] = 'Growth date cannot be before the stocking date.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.stock} growth on {self.recorded_date}'
