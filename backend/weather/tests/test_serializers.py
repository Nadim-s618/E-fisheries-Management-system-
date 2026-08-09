from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ponds.models import Pond
from weather.models import WeatherReport
from weather.serializers import WeatherReportSerializer


User = get_user_model()


class WeatherReportSerializerUnitTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='weather-serializer-owner',
            email='weather-serializer-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=user,
            name='Weather Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def create_report(self, **overrides):
        data = {
            'pond': self.pond,
            'location_query': 'Natore',
            'resolved_location': 'Natore, Rajshahi, BD',
            'country': 'BD',
            'latitude': Decimal('24.411000'),
            'longitude': Decimal('88.982000'),
            'timezone': 'UTC+06:00',
            'observed_at': timezone.now(),
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
            'pond_impact': {'summary': 'Low impact'},
            'feeding_recommendation': [{'status': 'ok'}],
            'do_prediction': {'night': 6.5},
            'rain_impact': {'overflow': 'Low'},
            'alerts': [],
            'forecast': [],
            'raw_payload': {},
        }
        data.update(overrides)
        return WeatherReport.objects.create(**data)

    def test_serializer_returns_valid_report_data(self):
        report = self.create_report()

        data = WeatherReportSerializer(report).data

        self.assertEqual(data['pond'], self.pond.id)
        self.assertEqual(data['pond_name'], 'Weather Pond')
        self.assertEqual(data['pond_location'], 'Natore')
        self.assertEqual(data['fish_weather_risk'], WeatherReport.RiskLevel.LOW)

    def test_serializer_marks_all_report_fields_read_only(self):
        serializer = WeatherReportSerializer()

        self.assertTrue(all(field.read_only for field in serializer.fields.values()))

    def test_serializer_ignores_input_data_because_report_is_read_only(self):
        serializer = WeatherReportSerializer(data={
            'pond': self.pond.id,
            'location_query': 'Changed location',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data, {})
