from django.test import SimpleTestCase

from weather.services.analysis import analyse_weather
from weather.services.openweather import build_location_candidates


class WeatherAnalysisTests(SimpleTestCase):
    def test_analyse_weather_marks_calm_weather_low_risk(self):
        current = {
            'time': '2026-07-27T06:00:00+00:00',
            'temperature_2m': 28,
            'relative_humidity_2m': 70,
            'precipitation': 0,
            'wind_speed_10m': 8,
            'cloud_cover': 20,
            'pressure_msl': 1012,
        }
        daily = {'uv_index_max': [5], 'precipitation_probability_max': [15]}
        hourly = {
            'time': ['2026-07-27T06:00:00+00:00', '2026-07-27T09:00:00+00:00'],
            'temperature_2m': [28, 29],
            'precipitation_probability': [10, 15],
            'precipitation': [0, 0],
            'wind_speed_10m': [8, 9],
            'cloud_cover': [20, 30],
            'interval_hours': 3,
        }

        analysis = analyse_weather(current=current, daily=daily, hourly=hourly)

        self.assertEqual(analysis['fish_weather_risk'], 'Low')
        self.assertEqual(analysis['disease_risk'], 'Low')
        self.assertEqual(
            analysis['alerts'],
            [{'level': 'ok', 'text': 'No bad weather warning for the next 24 hours'}],
        )
        self.assertEqual(analysis['feeding_recommendation'][0]['status'], 'ok')
        self.assertEqual(analysis['rain_impact']['overflow'], 'Low')

    def test_analyse_weather_escalates_heavy_rain_heat_and_low_do(self):
        current = {
            'time': '2026-07-27T06:00:00+00:00',
            'temperature_2m': 36,
            'relative_humidity_2m': 94,
            'precipitation': 3,
            'wind_speed_10m': 38,
            'cloud_cover': 90,
            'pressure_msl': 992,
        }
        daily = {'uv_index_max': [9], 'precipitation_probability_max': [95]}
        hourly = {
            'time': [
                '2026-07-27T06:00:00+00:00',
                '2026-07-27T09:00:00+00:00',
                '2026-07-27T12:00:00+00:00',
                '2026-07-27T15:00:00+00:00',
                '2026-07-27T18:00:00+00:00',
                '2026-07-27T21:00:00+00:00',
                '2026-07-28T00:00:00+00:00',
                '2026-07-28T03:00:00+00:00',
            ],
            'temperature_2m': [36, 36, 35, 34, 33, 32, 31, 30],
            'precipitation_probability': [95, 90, 85, 80, 75, 80, 90, 95],
            'precipitation': [5, 6, 4, 8, 5, 4, 5, 6],
            'wind_speed_10m': [38, 36, 34, 35, 30, 28, 25, 22],
            'cloud_cover': [90, 92, 95, 94, 88, 85, 90, 96],
            'interval_hours': 3,
        }

        analysis = analyse_weather(current=current, daily=daily, hourly=hourly)
        alert_texts = {alert['text'] for alert in analysis['alerts']}

        self.assertEqual(analysis['fish_weather_risk'], 'High')
        self.assertEqual(analysis['disease_risk'], 'High')
        self.assertEqual(analysis['rain_impact']['overflow'], 'High')
        self.assertEqual(analysis['do_prediction']['action'], 'Turn on aerator')
        self.assertIn('Overflow risk', alert_texts)
        self.assertIn('Heat stress risk for fish', alert_texts)

    def test_build_location_candidates_adds_comilla_variant(self):
        self.assertEqual(
            build_location_candidates('Cumilla Sadar', ['North Pond']),
            ['Cumilla Sadar', 'comilla Sadar', 'North Pond'],
        )
