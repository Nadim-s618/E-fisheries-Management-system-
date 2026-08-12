from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from market_analysis.models import MarketPriceSnapshot


class MarketPriceSnapshotModelUnitTests(SimpleTestCase):
    def test_default_demand_level_is_medium(self):
        self.assertEqual(
            MarketPriceSnapshot().demand_level,
            MarketPriceSnapshot.DemandLevel.MEDIUM,
        )

    def test_string_representation_contains_market_identity(self):
        snapshot = MarketPriceSnapshot(
            fish_name='Rui', division='Dhaka', recorded_date=date(2026, 8, 12),
            price_per_kg=Decimal('350.00'),
        )
        self.assertEqual(str(snapshot), 'Rui in Dhaka - 350.00 on 2026-08-12')

    def test_demand_choices_are_limited_to_supported_levels(self):
        choices = {value for value, label in MarketPriceSnapshot.DemandLevel.choices}
        self.assertEqual(choices, {'Low', 'Medium', 'High'})
        self.assertNotIn('Very high', choices)
