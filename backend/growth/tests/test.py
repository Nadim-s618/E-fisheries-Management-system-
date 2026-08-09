from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from ponds.models import Pond
from stocks.models import FishStock


User = get_user_model()


class GrowthApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='growth-owner',
            email='growth-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='North Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )
        self.stock = FishStock.objects.create(
            pond=self.pond,
            species='Rohu',
            batch_name='Rohu A',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=950,
            initial_average_weight_g=Decimal('10.00'),
            status=FishStock.Status.ACTIVE,
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_growth_record_rejects_date_before_stocking(self):
        self.authenticate()

        response = self.client.post(
            f'/api/stocks/{self.stock.id}/growth/',
            {
                'recorded_date': '2025-12-31',
                'sample_count': 20,
                'average_weight_g': '12.50',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('recorded_date', response.data)
