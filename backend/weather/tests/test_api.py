from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from ponds.models import Pond
from weather.models import WeatherReport
from weather.services.openweather import WeatherServiceError


User = get_user_model()


class WeatherDashboardApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='weather-api-owner',
            email='weather-api-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='other-weather-api-owner',
            email='other-weather-api-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = self.create_pond(self.user, name='North Pond')
        self.other_pond = self.create_pond(self.other_user, name='Other Pond')

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def create_pond(self, owner, **overrides):
        data = {
            'owner': owner,
            'name': 'Weather Pond',
            'location': 'Natore',
            'area_decimal': Decimal('24.00'),
            'average_depth_ft': Decimal('5.00'),
            'stocking_capacity': 2000,
        }
        data.update(overrides)
        return Pond.objects.create(**data)

    def create_report(self, pond=None, **overrides):
        observed_at = timezone.now()
        data = {
            'pond': pond or self.pond,
            'location_query': 'Natore',
            'resolved_location': 'Natore, Rajshahi, BD',
            'country': 'BD',
            'latitude': Decimal('24.411000'),
            'longitude': Decimal('88.982000'),
            'timezone': '+06:00',
            'observed_at': observed_at,
            'forecast_date': date(2026, 7, 27),
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

    def test_dashboard_requires_authentication(self):
        response = self.client.get(f'/api/weather/dashboard/?pond={self.pond.id}')

        self.assertEqual(response.status_code, 401)

    @patch('weather.views.get_or_refresh_weather_report')
    def test_dashboard_returns_serialized_report(self, get_or_refresh_weather_report):
        self.authenticate()
        report = self.create_report()
        get_or_refresh_weather_report.return_value = (report, False, None)

        response = self.client.get(f'/api/weather/dashboard/?pond={self.pond.id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['report']['id'], report.id)
        self.assertEqual(response.data['report']['pond_name'], 'North Pond')
        self.assertFalse(response.data['stale'])
        self.assertIsNone(response.data['source_error'])
        get_or_refresh_weather_report.assert_called_once_with(self.pond, force_refresh=False)

    @patch('weather.views.get_or_refresh_weather_report')
    def test_dashboard_passes_refresh_flag(self, get_or_refresh_weather_report):
        self.authenticate()
        report = self.create_report()
        get_or_refresh_weather_report.return_value = (report, False, None)

        response = self.client.get(f'/api/weather/dashboard/?pond={self.pond.id}&refresh=true')

        self.assertEqual(response.status_code, 200)
        get_or_refresh_weather_report.assert_called_once_with(self.pond, force_refresh=True)

    def test_dashboard_rejects_other_users_pond(self):
        self.authenticate()

        response = self.client.get(f'/api/weather/dashboard/?pond={self.other_pond.id}')

        self.assertEqual(response.status_code, 400)
        self.assertIn('pond', response.data)

    @patch('weather.views.get_or_refresh_weather_report')
    def test_dashboard_returns_bad_gateway_for_provider_error(self, get_or_refresh_weather_report):
        self.authenticate()
        get_or_refresh_weather_report.side_effect = WeatherServiceError('Provider unavailable.')

        response = self.client.get(f'/api/weather/dashboard/?pond={self.pond.id}')

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data['detail'], 'Provider unavailable.')
