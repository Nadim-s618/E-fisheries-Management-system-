from django.core.exceptions import ValidationError
from django.db import models

from ponds.models import Pond


class FishStock(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PARTIAL_HARVEST = 'partial_harvest', 'Partial harvest'
        HARVESTED = 'harvested', 'Harvested'

    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='stocks',
    )
    species = models.CharField(max_length=120)
    batch_name = models.CharField(max_length=120)
    stocking_date = models.DateField()
    initial_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()
    initial_average_weight_g = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'store'
        ordering = ['pond__name', '-stocking_date', 'species']
        constraints = [
            models.UniqueConstraint(
                fields=['pond', 'batch_name'],
                name='unique_stock_batch_name_per_pond',
            ),
            models.CheckConstraint(
                condition=models.Q(initial_quantity__gt=0),
                name='stock_initial_quantity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(current_quantity__gte=0),
                name='stock_current_quantity_not_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(initial_average_weight_g__gt=0),
                name='stock_initial_average_weight_positive',
            ),
        ]

    def clean(self):
        errors = {}

        if not (self.species or '').strip():
            errors['species'] = 'Fish species is required.'

        if not (self.batch_name or '').strip():
            errors['batch_name'] = 'Batch name is required.'

        if self.initial_quantity is not None and self.initial_quantity <= 0:
            errors['initial_quantity'] = 'Initial quantity must be greater than zero.'

        if self.current_quantity is not None and self.current_quantity < 0:
            errors['current_quantity'] = 'Current quantity cannot be negative.'

        if (
            self.initial_average_weight_g is not None
            and self.initial_average_weight_g <= 0
        ):
            errors['initial_average_weight_g'] = 'Initial average weight must be greater than zero.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.batch_name} - {self.species}'
