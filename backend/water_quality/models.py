from django.db import models

from ponds.models import Pond


class WaterQualityReading(models.Model):
    class OverallStatus(models.TextChoices):
        GOOD = 'Good', 'Good'
        WARNING = 'Warning', 'Warning'
        DANGER = 'Danger', 'Danger'

    pond = models.ForeignKey(
        Pond,
        verbose_name='Pond',
        on_delete=models.CASCADE,
        related_name='water_quality_readings',
    )
    temperature = models.FloatField(verbose_name='Water temperature')
    ph = models.FloatField(verbose_name='pH')
    dissolved_oxygen = models.FloatField(verbose_name='Dissolved oxygen')
    ammonia = models.FloatField(verbose_name='Ammonia')
    nitrite = models.FloatField(verbose_name='Nitrite')
    nitrate = models.FloatField(verbose_name='Nitrate')
    turbidity = models.FloatField(verbose_name='Turbidity')
    salinity = models.FloatField(
        verbose_name='Salinity',
        null=True,
        blank=True,
    )
    water_level = models.FloatField(verbose_name='Water level')
    overall_status = models.CharField(
        verbose_name='Overall status',
        max_length=16,
        choices=OverallStatus.choices,
        default=OverallStatus.GOOD,
    )
    created_at = models.DateTimeField(verbose_name='Created at', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='Updated at', auto_now=True)

    class Meta:
        verbose_name = 'Water quality reading'
        verbose_name_plural = 'Water quality readings'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.pond} - {self.overall_status} ({self.created_at:%Y-%m-%d %H:%M})'
