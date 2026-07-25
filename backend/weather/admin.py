from django.contrib import admin

from .models import WeatherReport


@admin.register(WeatherReport)
class WeatherReportAdmin(admin.ModelAdmin):
    list_display = (
        'pond',
        'resolved_location',
        'air_temperature',
        'rainfall_probability',
        'fish_weather_risk',
        'disease_risk',
        'observed_at',
    )
    list_filter = ('fish_weather_risk', 'disease_risk', 'source')
    search_fields = ('pond__name', 'location_query', 'resolved_location')
    readonly_fields = ('created_at', 'updated_at')
