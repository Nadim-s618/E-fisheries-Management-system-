from datetime import datetime, timezone

from django.test import SimpleTestCase

from ponds.models import Pond
from water_quality.models import WaterQualityReading


def make_reading(**overrides):
    defaults = {
        'pond_id': 1,
        'temperature': 28.0,
        'ph': 7.2,
        'dissolved_oxygen': 6.5,
        'ammonia': 0.01,
        'nitrite': 0.1,
        'nitrate': 25.0,
        'turbidity': 55.0,
        'salinity': 5.0,
        'water_level': 4.5,
        'created_at': datetime(2026, 7, 27, 6, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return WaterQualityReading(**defaults)


class WaterQualityReadingModelUnitTests(SimpleTestCase):
    def test_default_status_is_good(self):
        reading = make_reading()

        self.assertEqual(reading.overall_status, WaterQualityReading.OverallStatus.GOOD)

    def test_string_contains_pond_status_and_timestamp(self):
        reading = make_reading(overall_status=WaterQualityReading.OverallStatus.WARNING)
        reading._state.fields_cache['pond'] = Pond(
            owner_id=1,
            name='North Pond',
            location='Natore',
        )

        self.assertEqual(str(reading), 'North Pond - Warning (2026-07-27 06:00)')

    def test_status_choices_are_defined(self):
        self.assertEqual(WaterQualityReading.OverallStatus.GOOD.label, 'Good')
        self.assertEqual(WaterQualityReading.OverallStatus.WARNING.value, 'Warning')
        self.assertEqual(WaterQualityReading.OverallStatus.DANGER.value, 'Danger')

    def test_meta_configuration(self):
        self.assertEqual(WaterQualityReading._meta.ordering, ['-created_at'])
        self.assertEqual(
            WaterQualityReading._meta.verbose_name,
            'Water quality reading',
        )
        self.assertTrue(WaterQualityReading._meta.get_field('salinity').null)
        self.assertTrue(WaterQualityReading._meta.get_field('salinity').blank)

