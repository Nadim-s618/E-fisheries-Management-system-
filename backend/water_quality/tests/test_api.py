from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from ponds.models import Pond
from water_quality.models import WaterQualityReading
from water_quality.utils.thresholds import STATUS_DANGER, STATUS_GOOD, STATUS_WARNING
from water_quality.utils.trends import TREND_INCREASING


User = get_user_model()


class WaterQualityApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='water-owner',
            email='water-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='other-water-owner',
            email='other-water-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = self.create_pond(owner=self.user, name='North Pond')
        self.other_pond = self.create_pond(owner=self.other_user, name='Other Pond')

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def create_pond(self, owner, **overrides):
        data = {
            'owner': owner,
            'name': 'Test Pond',
            'location': 'Natore',
            'area_decimal': Decimal('24.00'),
            'average_depth_ft': Decimal('5.00'),
            'stocking_capacity': 2000,
        }
        data.update(overrides)
        return Pond.objects.create(**data)

    def create_reading(self, pond=None, **overrides):
        data = {
            'pond': pond or self.pond,
            'temperature': 28,
            'ph': 7.2,
            'dissolved_oxygen': 6.5,
            'ammonia': 0.01,
            'nitrite': 0.1,
            'nitrate': 25,
            'turbidity': 55,
            'salinity': 5,
            'water_level': 4.5,
            'overall_status': WaterQualityReading.OverallStatus.GOOD,
        }
        data.update(overrides)
        return WaterQualityReading.objects.create(**data)

    def reading_payload(self, **overrides):
        data = {
            'pond': self.pond.id,
            'temperature': 28,
            'ph': 7.2,
            'dissolved_oxygen': 6.5,
            'ammonia': 0.01,
            'nitrite': 0.1,
            'nitrate': 25,
            'turbidity': 55,
            'salinity': 5,
            'water_level': 4.5,
            'overall_status': WaterQualityReading.OverallStatus.GOOD,
        }
        data.update(overrides)
        return data

    def test_reading_list_requires_authentication(self):
        response = self.client.get('/api/water-quality/water-quality-readings/')

        self.assertEqual(response.status_code, 401)

    def test_create_reading_rejects_out_of_range_values(self):
        self.authenticate()

        response = self.client.post(
            '/api/water-quality/water-quality-readings/',
            self.reading_payload(ph=15),
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('ph', response.data)

    def test_user_only_lists_own_readings(self):
        self.authenticate()
        own_reading = self.create_reading()
        self.create_reading(pond=self.other_pond)

        response = self.client.get('/api/water-quality/water-quality-readings/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], own_reading.id)

    def test_dashboard_returns_latest_analysis_counts_and_trends(self):
        self.authenticate()
        self.create_reading(temperature=27, ph=7.0, dissolved_oxygen=6.5)
        latest = self.create_reading(
            temperature=35,
            ph=9.5,
            dissolved_oxygen=4,
            ammonia=0.01,
            nitrite=0.1,
            nitrate=25,
            turbidity=55,
            salinity=5,
            water_level=4.5,
        )

        response = self.client.get(f'/api/water-quality/dashboard/?pond={self.pond.id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['latest_reading']['id'], latest.id)
        self.assertEqual(response.data['overall_status'], STATUS_DANGER)
        self.assertEqual(response.data['danger_count'], 2)
        self.assertEqual(response.data['warning_count'], 1)
        self.assertEqual(response.data['good_count'], 6)

        cards = {
            card['parameter']: card
            for card in response.data['parameter_cards']
        }
        self.assertEqual(cards['temperature']['status'], STATUS_DANGER)
        self.assertEqual(cards['temperature']['trend'], TREND_INCREASING)
        self.assertEqual(cards['ph']['status'], STATUS_DANGER)
        self.assertEqual(cards['dissolved_oxygen']['status'], STATUS_WARNING)
        self.assertEqual(cards['ammonia']['status'], STATUS_GOOD)

    def test_dashboard_rejects_other_users_pond(self):
        self.authenticate()
        self.create_reading(pond=self.other_pond)

        response = self.client.get(f'/api/water-quality/dashboard/?pond={self.other_pond.id}')

        self.assertEqual(response.status_code, 404)
