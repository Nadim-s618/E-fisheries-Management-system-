from django.db import models

from ponds.models import Pond


class WeatherReport(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = 'Low', 'Low'
        MODERATE = 'Moderate', 'Moderate'
        HIGH = 'High', 'High'

    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='weather_reports',
    )
    location_query = models.CharField(max_length=180)
    resolved_location = models.CharField(max_length=220)
    country = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timezone = models.CharField(max_length=80, blank=True)
    observed_at = models.DateTimeField()
    forecast_date = models.DateField()
    air_temperature = models.FloatField()
    rainfall_probability = models.FloatField()
    rainfall_mm = models.FloatField()
    wind_speed = models.FloatField()
    humidity = models.FloatField()
    uv_index = models.FloatField(null=True, blank=True)
    cloud_cover = models.FloatField()
    atmospheric_pressure = models.FloatField()
    weather_code = models.IntegerField(null=True, blank=True)
    fish_weather_risk = models.CharField(
        max_length=16,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
    )
    disease_risk = models.CharField(
        max_length=16,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
    )
    pond_impact = models.JSONField(default=dict)
    feeding_recommendation = models.JSONField(default=list)
    do_prediction = models.JSONField(default=dict)
    rain_impact = models.JSONField(default=dict)
    alerts = models.JSONField(default=list)
    forecast = models.JSONField(default=list)
    raw_payload = models.JSONField(default=dict)
    source = models.CharField(max_length=80, default='OpenWeather')
    source_url = models.URLField(default='https://openweathermap.org/api')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-observed_at', '-created_at']
        indexes = [
            models.Index(fields=['pond', '-observed_at']),
        ]

    def __str__(self):
        return f'{self.pond} weather at {self.observed_at:%Y-%m-%d %H:%M}'
