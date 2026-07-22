from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Pond(models.Model):
    class WaterSource(models.TextChoices):
        RAINWATER = 'rainwater', 'Rainwater'
        RIVER = 'river', 'River'
        DEEP_TUBEWELL = 'deep_tubewell', 'Deep tubewell'
        CANAL = 'canal', 'Canal'
        MIXED = 'mixed', 'Mixed'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        MAINTENANCE = 'maintenance', 'Maintenance'
        INACTIVE = 'inactive', 'Inactive'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ponds',
    )
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=180)
    area_decimal = models.DecimalField(max_digits=8, decimal_places=2)
    average_depth_ft = models.DecimalField(max_digits=5, decimal_places=2)
    water_source = models.CharField(
        max_length=24,
        choices=WaterSource.choices,
        default=WaterSource.MIXED,
    )
    stocking_capacity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'store'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_pond_name_per_owner',
            ),
            models.CheckConstraint(
                condition=models.Q(area_decimal__gt=0),
                name='pond_area_decimal_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(average_depth_ft__gt=0),
                name='pond_average_depth_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(stocking_capacity__gt=0),
                name='pond_stocking_capacity_positive',
            ),
        ]

    def clean(self):
        errors = {}

        if self.area_decimal is not None and self.area_decimal <= 0:
            errors['area_decimal'] = 'Pond area must be greater than zero.'

        if self.average_depth_ft is not None and self.average_depth_ft <= 0:
            errors['average_depth_ft'] = 'Average depth must be greater than zero.'

        if self.stocking_capacity is not None and self.stocking_capacity <= 0:
            errors['stocking_capacity'] = 'Stocking capacity must be greater than zero.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name
