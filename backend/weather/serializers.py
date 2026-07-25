from rest_framework import serializers

from .models import WeatherReport


class WeatherReportSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)
    pond_location = serializers.CharField(source='pond.location', read_only=True)

    class Meta:
        model = WeatherReport
        fields = (
            'id',
            'pond',
            'pond_name',
            'pond_location',
            'location_query',
            'resolved_location',
            'country',
            'latitude',
            'longitude',
            'timezone',
            'observed_at',
            'forecast_date',
            'air_temperature',
            'rainfall_probability',
            'rainfall_mm',
            'wind_speed',
            'humidity',
            'uv_index',
            'cloud_cover',
            'atmospheric_pressure',
            'weather_code',
            'fish_weather_risk',
            'disease_risk',
            'pond_impact',
            'feeding_recommendation',
            'do_prediction',
            'rain_impact',
            'alerts',
            'forecast',
            'source',
            'source_url',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
