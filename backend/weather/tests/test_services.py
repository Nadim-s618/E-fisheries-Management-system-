from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from weather.services.notification_service import (
    build_current_value,
    build_parameter,
    build_reason,
)
from weather.services.openweather import (
    WeatherServiceError,
    build_location_candidates,
    format_timezone,
    get_api_key,
    meters_per_second_to_kmh,
    normalize_weather_code,
)


class OpenWeatherServiceUnitTests(SimpleTestCase):
    def test_build_location_candidates_returns_clean_unique_candidates(self):
        candidates = build_location_candidates(' Cumilla Sadar ', ['North Pond', 'cumilla sadar'])

        self.assertEqual(candidates, ['Cumilla Sadar', 'comilla Sadar', 'North Pond'])

    def test_build_location_candidates_rejects_short_terms(self):
        self.assertEqual(build_location_candidates(' ', ['A', None]), [])

    def test_normalize_weather_code_maps_clear_sky(self):
        self.assertEqual(normalize_weather_code(800), 0)

    def test_normalize_weather_code_handles_missing_code(self):
        self.assertIsNone(normalize_weather_code(None))

    def test_format_timezone_supports_positive_and_negative_offsets(self):
        self.assertEqual(format_timezone(21600), 'UTC+06:00')
        self.assertEqual(format_timezone(-19800), 'UTC-05:30')

    def test_meters_per_second_to_kmh_converts_speed(self):
        self.assertEqual(meters_per_second_to_kmh(10), 36.0)

    def test_meters_per_second_to_kmh_returns_none_for_missing_speed(self):
        self.assertIsNone(meters_per_second_to_kmh(None))

    @override_settings(OPENWEATHER_API_KEY='')
    def test_get_api_key_rejects_missing_key(self):
        with self.assertRaisesRegex(WeatherServiceError, 'API key is missing'):
            get_api_key()


class WeatherNotificationServiceUnitTests(SimpleTestCase):
    def setUp(self):
        self.report = SimpleNamespace(
            air_temperature=36,
            wind_speed=38,
            rainfall_probability=95,
            rain_impact={'next_24h_rain_mm': 35},
            do_prediction={'night': 4.8, 'unit': 'mg/L'},
            fish_weather_risk='High',
            pond=SimpleNamespace(name='North Pond'),
        )

    def test_build_parameter_maps_alerts_to_operational_parameters(self):
        self.assertEqual(build_parameter({'text': 'Overflow risk'}), 'Weather rainfall')
        self.assertEqual(build_parameter({'text': 'Heat stress risk for fish'}), 'Air temperature')
        self.assertEqual(build_parameter({'text': 'Strong wind warning'}), 'Wind speed')
        self.assertEqual(build_parameter({'text': 'Check aerator tonight'}), 'Predicted oxygen')

    def test_build_parameter_uses_generic_fallback_for_unknown_alert(self):
        self.assertEqual(build_parameter({'text': 'General notice'}), 'Weather alert')

    def test_build_current_value_formats_rainfall_alert(self):
        value = build_current_value(self.report, {'text': 'Overflow risk'})

        self.assertEqual(value, '35 mm next 24h, 95% chance')

    def test_build_reason_includes_alert_and_pond_name(self):
        reason = build_reason(self.report, {'text': 'Heat stress risk for fish'})

        self.assertIn('Heat stress risk for fish', reason)
        self.assertIn('North Pond', reason)

