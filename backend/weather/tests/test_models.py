from datetime import date, datetime, timezone
from decimal import Decimal

from django.test import SimpleTestCase

from ponds.models import Pond
from weather.models import WeatherReport


def make_report(**overrides):
    defaults = {
        'pond_id': 1,
        'location_query': 'Natore',
        'resolved_location': 'Natore, Rajshahi, BD',
        'country': 'BD',
        'latitude': Decimal('24.411000'),
        'longitude': Decimal('88.982000'),
        'timezone': 'UTC+06:00',
        'observed_at': datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc),
        'forecast_date': date(2026, 7, 27),
        'air_temperature': 28.0,
        'rainfall_probability': 20.0,
        'rainfall_mm': 0.0,
        'wind_speed': 8.0,
        'humidity': 70.0,
        'cloud_cover': 30.0,
        'atmospheric_pressure': 1012.0,
    }
    defaults.update(overrides)
    return WeatherReport(**defaults)


class WeatherReportModelUnitTests(SimpleTestCase):
    def test_string_contains_pond_and_observation_date(self):
        report = make_report()
        report._state.fields_cache['pond'] = Pond(
            owner_id=1,
            name='North Pond',
            location='Natore',
        )

        self.assertEqual(str(report), 'North Pond weather at 2026-07-27 06:00')

    def test_default_risks_are_low(self):
        report = make_report()

        self.assertEqual(report.fish_weather_risk, WeatherReport.RiskLevel.LOW)
        self.assertEqual(report.disease_risk, WeatherReport.RiskLevel.LOW)

    def test_json_fields_have_expected_defaults(self):
        report = make_report()

        self.assertEqual(report.pond_impact, {})
        self.assertEqual(report.do_prediction, {})
        self.assertEqual(report.raw_payload, {})
        self.assertEqual(report.feeding_recommendation, [])
        self.assertEqual(report.alerts, [])
        self.assertEqual(report.forecast, [])

    def test_risk_levels_are_valid_choices(self):
        self.assertEqual(WeatherReport.RiskLevel.LOW.label, 'Low')
        self.assertEqual(WeatherReport.RiskLevel.MODERATE.value, 'Moderate')
        self.assertEqual(WeatherReport.RiskLevel.HIGH.value, 'High')

    def test_meta_ordering_and_field_configuration(self):
        self.assertEqual(WeatherReport._meta.ordering, ['-observed_at', '-created_at'])
        self.assertEqual(WeatherReport._meta.get_field('location_query').max_length, 180)
        self.assertEqual(WeatherReport._meta.get_field('resolved_location').max_length, 220)
        self.assertEqual(WeatherReport._meta.get_field('latitude').decimal_places, 6)
        self.assertEqual(WeatherReport._meta.get_field('longitude').decimal_places, 6)
