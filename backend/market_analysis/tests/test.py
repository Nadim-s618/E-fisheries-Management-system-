from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from market_analysis.models import MarketPriceSnapshot
from market_analysis.services import (
    BANGLADESH_DIVISIONS,
    BANGLADESHI_FISH,
    SOURCE_GEMINI,
    SOURCE_SAMPLE,
    build_market_dashboard,
    ensure_market_data,
)

User = get_user_model()


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
        snapshot = MarketPriceSnapshot.objects.get(
            fish_name='Rui', division='Barishal', recorded_date=timezone.localdate(),
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
        mock_generate.assert_not_called()
        self.assertEqual(
            MarketPriceSnapshot.objects.count(),
            len(BANGLADESHI_FISH) * len(BANGLADESH_DIVISIONS) * 8,
        )
        dashboard = build_market_dashboard()
        self.assertEqual(dashboard['price_source'], SOURCE_SAMPLE)
        self.assertFalse(dashboard['ai_enabled'])

    def test_existing_snapshots_are_reused_without_regeneration(self):
        MarketPriceSnapshot.objects.create(
            fish_name='Rui', division='Dhaka', recorded_date=timezone.localdate(),
            price_per_kg=Decimal('350.00'),
        )
        with patch('market_analysis.services.build_sample_market_records') as mock_sample:
            result = ensure_market_data()
        self.assertFalse(result['generated'])
        self.assertEqual(result['source'], SOURCE_SAMPLE)
        mock_sample.assert_not_called()


class MarketAnalysisDashboardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='market-api-user', email='market-api@example.com', password='StrongPass123!',
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get('/api/market-analysis/dashboard/')
        self.assertEqual(response.status_code, 401)

    @override_settings(GEMINI_API_KEY='', GOOGLE_API_KEY='')
    def test_authenticated_dashboard_returns_market_summary(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/market-analysis/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['currency'], 'BDT')
        self.assertEqual(response.data['unit'], 'kg')
        self.assertEqual(response.data['price_source'], SOURCE_SAMPLE)
        self.assertIn('summary', response.data)
        self.assertIn('records', response.data)
        self.assertTrue(response.data['records'])

    @override_settings(GEMINI_API_KEY='', GOOGLE_API_KEY='')
    def test_dashboard_refresh_query_is_accepted(self):
        self.client.force_authenticate(self.user)
        first_response = self.client.get('/api/market-analysis/dashboard/')
        refresh_response = self.client.get('/api/market-analysis/dashboard/?refresh=true')
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(refresh_response.status_code, 200)
        self.assertEqual(
            refresh_response.data['summary']['market_points'],
            len(BANGLADESHI_FISH) * len(BANGLADESH_DIVISIONS),
        )
