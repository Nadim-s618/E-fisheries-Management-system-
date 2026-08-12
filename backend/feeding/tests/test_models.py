from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from feeding.models import FeedingRecommendation
from feeding.serializers import FeedingRecommendationEditSerializer, FeedingSessionCompleteSerializer


class FeedingModelUnitTests(SimpleTestCase):
    def test_recommendation_clean_accepts_positive_values(self):
        recommendation = FeedingRecommendation(
            recommended_feed_kg=Decimal('10.00'),
            price_per_kg=Decimal('135.00'),
            estimated_cost=Decimal('1350.00'),
            meals=2,
        )

        recommendation.clean()

        self.assertEqual(recommendation.meals, 2)

    def test_recommendation_clean_rejects_invalid_feed_price_and_meals(self):
        recommendation = FeedingRecommendation(
            recommended_feed_kg=Decimal('0.00'),
            price_per_kg=Decimal('-1.00'),
            estimated_cost=Decimal('0.00'),
            meals=0,
        )

        with self.assertRaises(ValidationError) as raised:
            recommendation.clean()

        self.assertEqual(
            set(raised.exception.message_dict),
            {'recommended_feed_kg', 'price_per_kg', 'meals'},
        )

    def test_edit_serializer_requires_meal_times_to_match_meals(self):
        serializer = FeedingRecommendationEditSerializer(data={
            'recommended_feed_kg': '10.00',
            'feed_type': 'Floating Feed 32%',
            'price_per_kg': '135.00',
            'meals': 3,
            'meal_times': ['08:00', '16:30'],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('meal_times', serializer.errors)

    def test_edit_serializer_accepts_a_valid_meal_plan(self):
        serializer = FeedingRecommendationEditSerializer(data={
            'recommended_feed_kg': '10.00',
            'feed_type': 'Floating Feed 32%',
            'price_per_kg': '135.00',
            'meals': 2,
            'meal_times': ['08:00', '16:30'],
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['meals'], 2)

    def test_session_completion_serializer_accepts_optional_values(self):
        serializer = FeedingSessionCompleteSerializer(data={
            'actual_feed_kg': '4.25',
            'notes': 'Fish consumed the full ration.',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['actual_feed_kg'], Decimal('4.25'))

    def test_edit_serializer_rejects_malformed_time(self):
        serializer = FeedingRecommendationEditSerializer(data={
            'recommended_feed_kg': '10.00',
            'feed_type': 'Floating Feed 32%',
            'price_per_kg': '135.00',
            'meals': 1,
            'meal_times': ['8:00'],
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('meal_times', serializer.errors)
