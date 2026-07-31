from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Notification
from growth.models import GrowthRecord
from ponds.models import Pond
from stocks.models import FishStock
from water_quality.models import WaterQualityReading
from weather.models import WeatherReport

from .models import FeedingRecommendation, FeedingSession


User = get_user_model()


class FeedingApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='feeding-owner',
            email='feeding-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='other-feeding-owner',
            email='other-feeding-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='Pond A',
            location='Natore',
            area_decimal=Decimal('32.00'),
            average_depth_ft=Decimal('5.50'),
            stocking_capacity=2500,
        )
        self.other_pond = Pond.objects.create(
            owner=self.other_user,
            name='Other Pond',
            location='Rajshahi',
            area_decimal=Decimal('20.00'),
            average_depth_ft=Decimal('4.50'),
            stocking_capacity=1200,
        )
        self.stock = FishStock.objects.create(
            pond=self.pond,
            species='Rohu',
            batch_name='Rohu A',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=1000,
            initial_average_weight_g=Decimal('100.00'),
            status=FishStock.Status.ACTIVE,
        )
        GrowthRecord.objects.create(
            stock=self.stock,
            recorded_date=date(2026, 7, 30),
            sample_count=30,
            average_weight_g=Decimal('700.00'),
            average_length_cm=Decimal('32.00'),
        )
        WaterQualityReading.objects.create(
            pond=self.pond,
            temperature=27.0,
            ph=7.2,
            dissolved_oxygen=7.8,
            ammonia=0.02,
            nitrite=0.01,
            nitrate=10.0,
            turbidity=22.0,
            water_level=1.3,
            overall_status=WaterQualityReading.OverallStatus.GOOD,
        )
        WeatherReport.objects.create(
            pond=self.pond,
            location_query='Natore',
            resolved_location='Natore',
            latitude=Decimal('24.420000'),
            longitude=Decimal('88.990000'),
            observed_at=timezone.now(),
            forecast_date=timezone.localdate(),
            air_temperature=29.0,
            rainfall_probability=0.1,
            rainfall_mm=0.0,
            wind_speed=8.0,
            humidity=72.0,
            cloud_cover=35.0,
            atmospheric_pressure=1010.0,
            fish_weather_risk=WeatherReport.RiskLevel.LOW,
            disease_risk=WeatherReport.RiskLevel.LOW,
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def test_dashboard_generates_recommendation_from_live_inputs(self):
        self.authenticate()

        response = self.client.get(f'/api/feeding/dashboard/?pond={self.pond.id}')

        self.assertEqual(response.status_code, 200)
        recommendation = response.data['recommendation']
        self.assertTrue(response.data['generated'])
        self.assertEqual(recommendation['pond_name'], 'Pond A')
        self.assertEqual(recommendation['feed_type'], 'Floating Feed 32%')
        self.assertEqual(recommendation['recommended_feed_kg'], '12.60')
        self.assertEqual(recommendation['estimated_cost'], '56.70')
        self.assertEqual(recommendation['meals'], 2)
        self.assertEqual(
            recommendation['reasons'],
            ['Water quality optimal', 'Good weather', 'Healthy fish'],
        )
        self.assertEqual(len(recommendation['schedule']), 2)
        self.assertTrue(Notification.objects.filter(user=self.user, parameter='Feeding recommendation').exists())

    def test_accept_recommendation_creates_trackable_sessions(self):
        self.authenticate()
        dashboard_response = self.client.get(f'/api/feeding/dashboard/?pond={self.pond.id}')
        recommendation_id = dashboard_response.data['recommendation']['id']

        response = self.client.post(f'/api/feeding/recommendations/{recommendation_id}/accept/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], FeedingRecommendation.Status.ACCEPTED)
        self.assertEqual(len(response.data['sessions']), 2)
        self.assertEqual(FeedingSession.objects.filter(recommendation_id=recommendation_id).count(), 2)
        self.assertTrue(Notification.objects.filter(user=self.user, parameter='Feeding schedule').exists())

    def test_complete_last_session_creates_next_recommendation(self):
        self.authenticate()
        dashboard_response = self.client.get(f'/api/feeding/dashboard/?pond={self.pond.id}')
        recommendation_id = dashboard_response.data['recommendation']['id']
        self.client.post(f'/api/feeding/recommendations/{recommendation_id}/accept/')
        sessions = list(FeedingSession.objects.filter(recommendation_id=recommendation_id).order_by('meal_number'))

        first_response = self.client.post(
            f'/api/feeding/sessions/{sessions[0].id}/complete/',
            {'actual_feed_kg': '6.30'},
            format='json',
        )
        final_response = self.client.post(
            f'/api/feeding/sessions/{sessions[1].id}/complete/',
            {'actual_feed_kg': '6.30'},
            format='json',
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertIsNotNone(first_response.data['next_session'])
        self.assertIsNone(first_response.data['next_recommendation'])
        self.assertEqual(final_response.status_code, 200)
        self.assertIsNone(final_response.data['next_session'])
        self.assertIsNotNone(final_response.data['next_recommendation'])
        self.assertEqual(final_response.data['recommendation']['status'], FeedingRecommendation.Status.COMPLETED)
        self.assertTrue(Notification.objects.filter(user=self.user, parameter='Feeding completed').exists())

    def test_user_cannot_access_other_users_feeding_dashboard(self):
        self.authenticate()

        response = self.client.get(f'/api/feeding/dashboard/?pond={self.other_pond.id}')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['pond'], 'Pond not found.')
