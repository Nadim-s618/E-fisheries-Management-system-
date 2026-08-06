from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from .models import MarketPriceSnapshot
from .services import (
    BANGLADESHI_FISH,
    BANGLADESH_DIVISIONS,
    SOURCE_GEMINI,
    SOURCE_SAMPLE,
    build_market_dashboard,
    ensure_market_data,
)


class MarketAnalysisGenerationTests(TestCase):
    def build_gemini_response(self):
        records = []
        for fish_index, fish in enumerate(BANGLADESHI_FISH):
            for division_index, division in enumerate(BANGLADESH_DIVISIONS):
                base_price = fish['base_price'] + division_index * 4 + fish_index
                records.append({
                    'fish_name': fish['name'],
                    'division': division,
                    'prices': [base_price + day_index for day_index in range(8)],
                    'demand_levels': ['Medium'] * 7 + ['High'],
                })
        return {'records': records}

    @override_settings(GEMINI_API_KEY='test-key', GOOGLE_API_KEY='')
    @patch('market_analysis.services.generate_json_response')
    def test_uses_gemini_to_generate_market_price_snapshots(self, mock_generate):
        mock_generate.return_value = self.build_gemini_response()

        result = ensure_market_data()

        self.assertEqual(result['source'], SOURCE_GEMINI)
        self.assertTrue(result['generated'])
        self.assertEqual(
            MarketPriceSnapshot.objects.count(),
            len(BANGLADESHI_FISH) * len(BANGLADESH_DIVISIONS) * 8,
        )

        today = timezone.localdate()
        snapshot = MarketPriceSnapshot.objects.get(
            fish_name='Rui',
            division='Barishal',
            recorded_date=today,
        )
        self.assertEqual(snapshot.price_per_kg, Decimal('337.00'))
        self.assertEqual(snapshot.demand_level, MarketPriceSnapshot.DemandLevel.HIGH)
        self.assertEqual(snapshot.source, SOURCE_GEMINI)

        dashboard = build_market_dashboard()
        self.assertEqual(dashboard['price_source'], SOURCE_GEMINI)
        self.assertTrue(dashboard['ai_enabled'])

    @override_settings(GEMINI_API_KEY='', GOOGLE_API_KEY='')
    @patch('market_analysis.services.generate_json_response')
    def test_falls_back_to_sample_prices_without_gemini_key(self, mock_generate):
        result = ensure_market_data()

        self.assertEqual(result['source'], SOURCE_SAMPLE)
        self.assertTrue(result['generated'])
        self.assertFalse(mock_generate.called)
        self.assertEqual(
            MarketPriceSnapshot.objects.count(),
            len(BANGLADESHI_FISH) * len(BANGLADESH_DIVISIONS) * 8,
        )

        dashboard = build_market_dashboard()
        self.assertEqual(dashboard['price_source'], SOURCE_SAMPLE)
        self.assertFalse(dashboard['ai_enabled'])
