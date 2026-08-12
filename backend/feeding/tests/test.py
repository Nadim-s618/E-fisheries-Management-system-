from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Notification
from feeding.models import FeedingRecommendation, FeedingSession
from growth.models import GrowthRecord
from ponds.models import Pond
from stocks.models import FishStock
from water_quality.models import WaterQualityReading
from weather.models import WeatherReport


BASE_URL = '/api/feeding/'


class FeedingAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username='feeding-owner', password='pass')
        self.other_user = user_model.objects.create_user(username='other-feeding-owner', password='pass')
        self.pond = self.create_pond(self.user, 'Pond A')
        self.other_pond = self.create_pond(self.other_user, 'Other Pond')
        self.stock = FishStock.objects.create(
            pond=self.pond, species='Rohu', batch_name='Rohu A', stocking_date=date(2026, 1, 1),
            initial_quantity=1000, current_quantity=1000,
            initial_average_weight_g=Decimal('100.00'),
        )
        GrowthRecord.objects.create(
            stock=self.stock, recorded_date=date(2026, 7, 30), sample_count=30,
            average_weight_g=Decimal('700.00'), average_length_cm=Decimal('32.00'),
        )
        WaterQualityReading.objects.create(
            pond=self.pond, temperature=27.0, ph=7.2, dissolved_oxygen=7.8,
            ammonia=0.02, nitrite=0.01, nitrate=10.0, turbidity=22.0,
            water_level=1.3, overall_status=WaterQualityReading.OverallStatus.GOOD,
        )
        WeatherReport.objects.create(
            pond=self.pond, location_query='Natore', resolved_location='Natore',
            latitude=Decimal('24.420000'), longitude=Decimal('88.990000'),
            observed_at=timezone.now(), forecast_date=timezone.localdate(),
            air_temperature=29.0, rainfall_probability=0.1, rainfall_mm=0.0,
            wind_speed=8.0, humidity=72.0, cloud_cover=35.0, atmospheric_pressure=1010.0,
            fish_weather_risk=WeatherReport.RiskLevel.LOW, disease_risk=WeatherReport.RiskLevel.LOW,
        )

    def create_pond(self, owner, name):
        return Pond.objects.create(
            owner=owner, name=name, location='Natore', area_decimal=Decimal('20.00'),
            average_depth_ft=Decimal('5.00'), stocking_capacity=1000,
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.user)

    def get_recommendation(self):
        response = self.client.get(f'{BASE_URL}dashboard/?pond={self.pond.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data['recommendation']

    def test_dashboard_requires_pond_and_generates_recommendation(self):
        self.authenticate()
        missing = self.client.get(f'{BASE_URL}dashboard/')
        response = self.client.get(f'{BASE_URL}dashboard/?pond={self.pond.id}')

        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['recommendation']['recommended_feed_kg'], '12.60')
        self.assertEqual(response.data['recommendation']['estimated_cost'], '1701.00')
        self.assertTrue(response.data['generated'])

    def test_dashboard_hides_another_users_pond(self):
        self.authenticate()

        response = self.client.get(f'{BASE_URL}dashboard/?pond={self.other_pond.id}')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['pond'], 'Pond not found.')

    def test_accept_recommendation_creates_sessions_and_is_idempotent(self):
        self.authenticate()
        recommendation_id = self.get_recommendation()['id']

        first = self.client.post(f'{BASE_URL}recommendations/{recommendation_id}/accept/')
        second = self.client.post(f'{BASE_URL}recommendations/{recommendation_id}/accept/')

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(FeedingSession.objects.filter(recommendation_id=recommendation_id).count(), 2)
        self.assertTrue(Notification.objects.filter(parameter='Feeding schedule').exists())

    def test_edit_recommendation_rebuilds_sessions(self):
        self.authenticate()
        recommendation_id = self.get_recommendation()['id']
        response = self.client.patch(
            f'{BASE_URL}recommendations/{recommendation_id}/edit/',
            {
                'recommended_feed_kg': '20.00', 'feed_type': 'Sinking Feed',
                'price_per_kg': '150.00', 'meals': 3,
                'meal_times': ['07:00', '13:00', '19:00'],
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], FeedingRecommendation.Status.EDITED)
        self.assertEqual(response.data['estimated_cost'], '3000.00')
        self.assertEqual(len(response.data['sessions']), 3)

    def test_complete_session_creates_financial_record_and_next_plan(self):
        self.authenticate()
        recommendation_id = self.get_recommendation()['id']
        self.client.post(f'{BASE_URL}recommendations/{recommendation_id}/accept/')
        sessions = list(FeedingSession.objects.filter(recommendation_id=recommendation_id).order_by('meal_number'))

        with patch('financials.services.create_automatic_financial_record') as create_record:
            first = self.client.post(
                f'{BASE_URL}sessions/{sessions[0].id}/complete/',
                {'actual_feed_kg': '6.30'}, format='json',
            )
            final = self.client.post(
                f'{BASE_URL}sessions/{sessions[1].id}/complete/',
                {'actual_feed_kg': '6.30'}, format='json',
            )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(first.data['next_session'])
        self.assertEqual(final.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(final.data['next_recommendation'])
        self.assertEqual(final.data['recommendation']['status'], FeedingRecommendation.Status.COMPLETED)
        self.assertEqual(create_record.call_count, 2)

    def test_complete_session_rejects_non_positive_actual_feed(self):
        self.authenticate()
        recommendation_id = self.get_recommendation()['id']
        self.client.post(f'{BASE_URL}recommendations/{recommendation_id}/accept/')
        session = FeedingSession.objects.filter(recommendation_id=recommendation_id).first()

        response = self.client.post(
            f'{BASE_URL}sessions/{session.id}/complete/', {'actual_feed_kg': '0.00'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('actual_feed_kg', response.data)
