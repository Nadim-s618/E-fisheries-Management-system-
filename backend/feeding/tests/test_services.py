from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from core.models import Notification
from feeding.services.notifications import create_feeding_notification
from feeding.services.recommendations import (
    build_schedule,
    enhance_payload_with_ai,
    get_feeding_rate,
    get_feeding_ai_advice,
    get_or_create_draft_recommendation,
    get_stock_summary,
)
from feeding.services.strategies import get_feeding_strategy_for_species
from feeding.models import FeedingRecommendation
from growth.models import GrowthRecord
from ponds.models import Pond
from stocks.models import FishStock


class FeedingCalculationUnitTests(SimpleTestCase):
    def test_missing_species_uses_general_strategy(self):
        strategy = get_feeding_strategy_for_species()

        self.assertEqual(strategy.name, 'general')
        self.assertEqual(strategy.get_feeding_rate(100), Decimal('0.030'))

    def test_fish_species_uses_fish_strategy(self):
        strategy = get_feeding_strategy_for_species('Tilapia')

        self.assertEqual(strategy.name, 'fish')
        self.assertEqual(strategy.get_meal_times(Decimal('1.00')), ['08:00', '16:30'])

    def test_shrimp_strategy_uses_species_specific_rate_and_meals(self):
        strategy = get_feeding_strategy_for_species('Whiteleg Shrimp')

        self.assertEqual(strategy.name, 'shrimp')
        self.assertEqual(strategy.get_feeding_rate(10), Decimal('0.060'))
        self.assertEqual(len(strategy.get_meal_times(Decimal('1.00'))), 3)

    def test_feed_rate_bands_match_fish_size(self):
        self.assertEqual(get_feeding_rate(Decimal('49.99')), Decimal('0.040'))
        self.assertEqual(get_feeding_rate(Decimal('100.00')), Decimal('0.030'))
        self.assertEqual(get_feeding_rate(Decimal('300.00')), Decimal('0.025'))
        self.assertEqual(get_feeding_rate(Decimal('500.00')), Decimal('0.018'))

    def test_build_schedule_allocates_rounding_remainder_to_last_meal(self):
        schedule = build_schedule(date(2026, 8, 1), Decimal('10.00'), ['08:00', '16:30', '20:00'])

        self.assertEqual([item['feed_kg'] for item in schedule], ['3.33', '3.33', '3.34'])
        self.assertEqual([item['label'] for item in schedule], ['8:00 AM', '4:30 PM', '8:00 PM'])

    @patch('feeding.services.recommendations.is_gemini_configured', return_value=False)
    def test_ai_advice_falls_back_to_formula_guidance(self, configured):
        advice = get_feeding_ai_advice(object(), {})

        self.assertEqual(advice['source'], 'fallback')
        self.assertFalse(advice['ai_enabled'])
        self.assertTrue(advice['recommendations'])
        configured.assert_called_once_with()


class FeedingServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='feeding-service-user', password='pass')
        self.pond = Pond.objects.create(
            owner=self.user, name='Service Pond', location='Natore',
            area_decimal=Decimal('20.00'), average_depth_ft=Decimal('5.00'), stocking_capacity=1000,
        )
        self.stock = FishStock.objects.create(
            pond=self.pond, species='Rohu', batch_name='Rohu A', stocking_date=date(2026, 1, 1),
            initial_quantity=1000, current_quantity=1000,
            initial_average_weight_g=Decimal('100.00'),
        )

    def test_stock_summary_uses_growth_weight_then_stock_weight(self):
        GrowthRecord.objects.create(
            stock=self.stock, recorded_date=date(2026, 7, 30), sample_count=30,
            average_weight_g=Decimal('700.00'), average_length_cm=Decimal('32.00'),
        )
        current_growth = get_stock_summary(self.pond)
        GrowthRecord.objects.all().delete()
        stock_weight = get_stock_summary(self.pond)

        self.assertEqual(current_growth['weight_source'], 'current_growth')
        self.assertEqual(current_growth['biomass_kg'], Decimal('700.00'))
        self.assertEqual(stock_weight['weight_source'], 'stock_initial_weight')
        self.assertEqual(stock_weight['biomass_kg'], Decimal('100.00'))

    def test_stock_summary_selects_strategy_from_active_species(self):
        self.stock.species = 'Whiteleg Shrimp'
        self.stock.initial_average_weight_g = Decimal('10.00')
        self.stock.save(update_fields=['species', 'initial_average_weight_g'])

        summary = get_stock_summary(self.pond)

        self.assertEqual(summary['strategy'], 'shrimp')
        self.assertEqual(summary['feeding_rate'], Decimal('0.060'))

    def test_draft_recommendation_is_reused(self):
        first, generated = get_or_create_draft_recommendation(self.pond)
        second, regenerated = get_or_create_draft_recommendation(self.pond)

        self.assertTrue(generated)
        self.assertFalse(regenerated)
        self.assertEqual(first.pk, second.pk)

    @patch('feeding.services.recommendations.is_gemini_configured', return_value=True)
    @patch('feeding.services.recommendations.generate_json_response')
    def test_gemini_price_is_clamped_into_safe_range(self, generate_json_response, configured):
        generate_json_response.return_value = {'price_per_kg': '999'}
        payload = {
            'recommendation_date': date(2026, 8, 1),
            'recommended_feed_kg': Decimal('10.00'),
            'price_per_kg': Decimal('135.00'),
            'estimated_cost': Decimal('1350.00'),
            'schedule': [{'time': '08:00'}, {'time': '16:30'}],
            'reasons': ['Healthy fish'], 'input_summary': {},
        }

        result = enhance_payload_with_ai(self.pond, payload)

        self.assertEqual(result['price_per_kg'], Decimal('300.00'))
        self.assertEqual(result['estimated_cost'], Decimal('3000.00'))
        configured.assert_called_once_with()

    def test_feeding_notification_is_deduplicated(self):
        first = create_feeding_notification(self.pond, 'Feeding test', '10 kg', 'Test notification')
        second = create_feeding_notification(self.pond, 'Feeding test', '10 kg', 'Test notification')

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(Notification.objects.filter(parameter='Feeding test').count(), 1)

    def test_feeding_notification_is_created_for_a_new_event(self):
        notification = create_feeding_notification(
            self.pond, 'Feeding ready', '12.60 kg', 'New recommendation is ready.',
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.pond, self.pond)
        self.assertFalse(notification.is_read)
