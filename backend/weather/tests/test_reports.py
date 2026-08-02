from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from ponds.models import Pond
from weather.models import WeatherReport
from weather.services.openweather import WeatherServiceError
from weather.services.reports import get_or_refresh_weather_report


User = get_user_model()


class WeatherReportServiceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='weather-owner',
            email='weather-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='North Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def create_report(self, **overrides):
        observed_at = timezone.now()
        data = {
            'pond': self.pond,
            'location_query': self.pond.location,
            'resolved_location': 'Natore, Rajshahi, BD',
            'country': 'BD',
            'latitude': Decimal('24.411000'),
            'longitude': Decimal('88.982000'),
            'timezone': '+06:00',
            'observed_at': observed_at,
            'forecast_date': observed_at.date(),
            'air_temperature': 28,
            'rainfall_probability': 20,
            'rainfall_mm': 0,
            'wind_speed': 8,
            'humidity': 70,
            'uv_index': 5,
            'cloud_cover': 30,
            'atmospheric_pressure': 1012,
            'weather_code': 0,
            'fish_weather_risk': WeatherReport.RiskLevel.LOW,
            'disease_risk': WeatherReport.RiskLevel.LOW,
            'pond_impact': {'summary': 'Low impact', 'items': ['Low impact']},
            'feeding_recommendation': [{'status': 'ok', 'text': 'Feed at 6 AM'}],
            'do_prediction': {'morning': 7.8, 'night': 6.5, 'unit': 'mg/L'},
            'rain_impact': {'overflow': 'Low'},
            'alerts': [{'level': 'ok', 'text': 'No bad weather warning'}],
            'forecast': [],
            'raw_payload': {},
        }
        data.update(overrides)
        return WeatherReport.objects.create(**data)

    @override_settings(WEATHER_REPORT_CACHE_MINUTES=30)
    @patch('weather.services.reports.fetch_forecast')
    @patch('weather.services.reports.geocode_location')
    def test_get_or_refresh_reuses_fresh_report_without_provider_call(
        self,
        geocode_location,
        fetch_forecast,
    ):
        report = self.create_report()

        returned_report, is_stale, source_error = get_or_refresh_weather_report(self.pond)

        self.assertEqual(returned_report.pk, report.pk)
        self.assertFalse(is_stale)
        self.assertIsNone(source_error)
        geocode_location.assert_not_called()
        fetch_forecast.assert_not_called()

    @override_settings(WEATHER_REPORT_CACHE_MINUTES=30)
    @patch('weather.services.reports.create_weather_report')
    def test_get_or_refresh_returns_stale_report_when_provider_fails(self, create_weather_report):
        report = self.create_report()
        WeatherReport.objects.filter(pk=report.pk).update(
            updated_at=timezone.now() - timedelta(minutes=45),
        )
        create_weather_report.side_effect = WeatherServiceError('Provider unavailable.')

        returned_report, is_stale, source_error = get_or_refresh_weather_report(self.pond)

        self.assertEqual(returned_report.pk, report.pk)
        self.assertTrue(is_stale)
        self.assertEqual(source_error, 'Provider unavailable.')

    @patch('weather.services.reports.fetch_forecast')
    @patch('weather.services.reports.geocode_location')
    def test_create_report_from_provider_payload(self, geocode_location, fetch_forecast):
        geocode_location.return_value = {
            'name': 'Natore',
            'admin1': 'Rajshahi',
            'country': 'BD',
            'latitude': 24.411,
            'longitude': 88.982,
            'timezone': '',
        }
        fetch_forecast.return_value = {
            'timezone': '+06:00',
            'current': {
                'time': '2026-07-27T06:00:00+00:00',
                'temperature_2m': 28.4,
                'relative_humidity_2m': 72,
                'precipitation': 0.2,
                'wind_speed_10m': 9.1,
                'cloud_cover': 35,
                'pressure_msl': 1011.6,
                'weather_code': 2,
            },
            'daily': {
                'uv_index_max': [6.2],
                'precipitation_probability_max': [30],
            },
            'hourly': {
                'time': ['2026-07-27T06:00:00+00:00'],
                'temperature_2m': [28.4],
                'precipitation_probability': [30],
                'precipitation': [0.2],
                'wind_speed_10m': [9.1],
                'cloud_cover': [35],
                'interval_hours': 3,
            },
        }

        report, is_stale, source_error = get_or_refresh_weather_report(
            self.pond,
            force_refresh=True,
        )

        self.assertFalse(is_stale)
        self.assertIsNone(source_error)
        self.assertEqual(report.pond, self.pond)
        self.assertEqual(report.location_query, 'Natore')
        self.assertEqual(report.resolved_location, 'Natore, Rajshahi, BD')
        self.assertEqual(report.air_temperature, 28.4)
        self.assertEqual(report.rainfall_probability, 30)
        self.assertEqual(report.source, 'OpenWeather')
        geocode_location.assert_called_once_with('Natore', fallback_terms=['North Pond'])
        fetch_forecast.assert_called_once_with(24.411, 88.982)
