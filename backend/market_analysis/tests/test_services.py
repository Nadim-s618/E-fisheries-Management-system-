from datetime import date
from decimal import Decimal, InvalidOperation
from unittest.mock import patch

from django.test import SimpleTestCase

from market_analysis.models import MarketPriceSnapshot
from market_analysis.services import (
    BANGLADESH_DIVISIONS, BANGLADESHI_FISH, DEMAND_LEVELS, SOURCE_SAMPLE,
    build_gemini_market_records, build_market_generation_prompt,
    build_sample_market_records, calculate_prediction_step, normalize_choice,
    normalize_demand_level, normalize_price, round_decimal,
)


class MarketAnalysisServiceUnitTests(SimpleTestCase):
    def test_normalize_choice_accepts_case_and_whitespace_variations(self):
        self.assertEqual(normalize_choice('  DHAKA ', BANGLADESH_DIVISIONS), 'Dhaka')

    def test_normalize_choice_returns_none_for_unknown_or_empty_values(self):
        self.assertIsNone(normalize_choice('Comilla', BANGLADESH_DIVISIONS))
        self.assertIsNone(normalize_choice('', BANGLADESH_DIVISIONS))

    def test_normalize_price_accepts_lower_and_upper_boundaries(self):
        self.assertEqual(normalize_price('80'), Decimal('80.00'))
        self.assertEqual(normalize_price('5000'), Decimal('5000.00'))

    def test_normalize_price_rejects_out_of_range_values(self):
        with self.assertRaises(ValueError):
            normalize_price('79.99')
        with self.assertRaises(ValueError):
            normalize_price('5000.01')

    def test_normalize_price_rejects_non_numeric_values(self):
        with self.assertRaises((InvalidOperation, ValueError)):
            normalize_price('not-a-price')

    def test_normalize_demand_level_accepts_supported_values(self):
        self.assertEqual(normalize_demand_level(' low '), MarketPriceSnapshot.DemandLevel.LOW)
        self.assertEqual(normalize_demand_level('Medium'), MarketPriceSnapshot.DemandLevel.MEDIUM)
        self.assertEqual(normalize_demand_level('HIGH'), MarketPriceSnapshot.DemandLevel.HIGH)

    def test_normalize_demand_level_rejects_unknown_value(self):
        with self.assertRaisesRegex(ValueError, 'invalid demand level'):
            normalize_demand_level('Very high')

    def test_round_decimal_returns_two_decimal_places_as_float(self):
        self.assertEqual(round_decimal(Decimal('123.456')), 123.46)

    def test_sample_market_records_cover_eight_days_and_all_market_pairs(self):
        records = build_sample_market_records(date(2026, 8, 12))
        self.assertEqual(len(records), len(BANGLADESHI_FISH) * len(BANGLADESH_DIVISIONS) * 8)
        self.assertEqual(min(record.recorded_date for record in records), date(2026, 8, 5))
        self.assertEqual(max(record.recorded_date for record in records), date(2026, 8, 12))
        self.assertTrue(all(record.source == SOURCE_SAMPLE for record in records))
        self.assertTrue(all(record.price_per_kg >= Decimal('80') for record in records))
        self.assertTrue(all(record.demand_level in DEMAND_LEVELS for record in records))

    def test_prediction_step_is_zero_for_insufficient_history(self):
        self.assertEqual(calculate_prediction_step([]), Decimal('0.00'))
        self.assertEqual(calculate_prediction_step([
            type('Snapshot', (), {'price_per_kg': Decimal('250')})(),
        ]), Decimal('0.00'))

    def test_prediction_step_calculates_positive_and_negative_trends(self):
        rising = [type('Snapshot', (), {'price_per_kg': value})() for value in (
            Decimal('100'), Decimal('110'), Decimal('130'),
        )]
        falling = [type('Snapshot', (), {'price_per_kg': value})() for value in (
            Decimal('130'), Decimal('110'), Decimal('100'),
        )]
        self.assertEqual(calculate_prediction_step(rising), Decimal('15'))
        self.assertEqual(calculate_prediction_step(falling), Decimal('-15'))

    def test_generation_prompt_contains_required_market_dimensions(self):
        prompt = build_market_generation_prompt(date(2026, 8, 12))
        self.assertIn('Bangladesh', prompt)
        self.assertIn('records', prompt)
        self.assertIn('Rui', prompt)
        self.assertIn('Dhaka', prompt)
        self.assertIn('2026-08-12', prompt)

    @patch('market_analysis.services.generate_json_response')
    def test_gemini_records_reject_missing_fish_division_pairs(self, mock_generate):
        mock_generate.return_value = {'records': []}
        with self.assertRaisesRegex(ValueError, 'missing fish/division combinations'):
            build_gemini_market_records(date(2026, 8, 12))

    @patch('market_analysis.services.generate_json_response')
    def test_gemini_records_reject_wrong_price_series_length(self, mock_generate):
        mock_generate.return_value = {'records': [{
            'fish_name': 'Rui', 'division': 'Dhaka', 'prices': [300], 'demand_levels': ['Low'] * 8,
        }]}
        with self.assertRaisesRegex(ValueError, 'missing fish/division combinations'):
            build_gemini_market_records(date(2026, 8, 12))
