from django.test import SimpleTestCase

from water_quality.services.analyser import analyse_water_quality
from water_quality.utils.thresholds import STATUS_DANGER, STATUS_GOOD, STATUS_WARNING
from water_quality.utils.trends import (
    TREND_DECREASING,
    TREND_INCREASING,
    TREND_STABLE,
    calculate_trend,
    calculate_trends,
)


class WaterQualityAnalysisTests(SimpleTestCase):
    def test_analyse_water_quality_marks_safe_values_good(self):
        analysis = analyse_water_quality(
            temperature=28,
            ph=7.2,
            dissolved_oxygen=6.5,
            ammonia=0.01,
            nitrite=0.1,
            nitrate=25,
            turbidity=55,
            salinity=None,
            water_level=4.5,
        )

        self.assertEqual(analysis['overall_status'], STATUS_GOOD)
        self.assertEqual(len(analysis['parameters']), 8)
        self.assertTrue(
            all(parameter['status'] == STATUS_GOOD for parameter in analysis['parameters']),
        )

    def test_analyse_water_quality_escalates_overall_status_to_danger(self):
        analysis = analyse_water_quality(
            temperature=35,
            ph=7.2,
            dissolved_oxygen=4,
            ammonia=0.08,
            nitrite=0.1,
            nitrate=25,
            turbidity=55,
            salinity=10,
            water_level=4.5,
        )
        statuses = {
            parameter['parameter']: parameter['status']
            for parameter in analysis['parameters']
        }

        self.assertEqual(analysis['overall_status'], STATUS_DANGER)
        self.assertEqual(statuses['temperature'], STATUS_DANGER)
        self.assertEqual(statuses['dissolved_oxygen'], STATUS_WARNING)
        self.assertEqual(statuses['ammonia'], STATUS_DANGER)

    def test_calculate_trends_handles_dicts_and_missing_values(self):
        latest = {
            'temperature': 30,
            'ph': 7.1,
            'dissolved_oxygen': 6,
            'ammonia': 0.01,
            'nitrite': 0.1,
            'nitrate': 30,
            'turbidity': 60,
            'salinity': None,
            'water_level': 4,
        }
        previous = {
            'temperature': 28,
            'ph': 7.5,
            'dissolved_oxygen': 6,
            'ammonia': 0.02,
            'nitrite': 0.1,
            'nitrate': 25,
            'turbidity': 70,
            'salinity': 5,
            'water_level': 4,
        }

        trends = calculate_trends(latest, previous)

        self.assertEqual(trends['temperature'], TREND_INCREASING)
        self.assertEqual(trends['ph'], TREND_DECREASING)
        self.assertEqual(trends['dissolved_oxygen'], TREND_STABLE)
        self.assertEqual(trends['salinity'], TREND_STABLE)
        self.assertEqual(calculate_trend(None, 4), TREND_STABLE)
