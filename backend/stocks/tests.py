from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from growth.models import GrowthRecord
from ponds.models import Pond

from .models import FishStock


User = get_user_model()


class StockApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='stock-owner',
            email='stock-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='other-stock-owner',
            email='other-stock-owner@example.com',
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
        self.other_pond = Pond.objects.create(
            owner=self.other_user,
            name='Other Pond',
            location='Rajshahi',
            area_decimal=Decimal('18.00'),
            average_depth_ft=Decimal('4.50'),
            stocking_capacity=1200,
        )
        self.stock_payload = {
            'species': 'Rohu',
            'batch_name': 'Rohu A',
            'stocking_date': '2026-01-01',
            'initial_quantity': 1000,
            'current_quantity': 950,
            'initial_average_weight_g': '10.00',
            'status': 'active',
            'notes': 'First batch.',
        }

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def create_stock(self, pond=None, **overrides):
        data = {
            'pond': pond or self.pond,
            'species': 'Rohu',
            'batch_name': 'Rohu A',
            'stocking_date': date(2026, 1, 1),
            'initial_quantity': 1000,
            'current_quantity': 950,
            'initial_average_weight_g': Decimal('10.00'),
            'status': FishStock.Status.ACTIVE,
        }
        data.update(overrides)
        return FishStock.objects.create(**data)

    def test_stock_list_requires_authentication(self):
        response = self.client.get(f'/api/ponds/{self.pond.id}/stocks/')

        self.assertEqual(response.status_code, 401)

    def test_create_stock_allows_same_species_different_batches(self):
        self.authenticate()

        first_response = self.client.post(
            f'/api/ponds/{self.pond.id}/stocks/',
            self.stock_payload,
            format='json',
        )
        second_response = self.client.post(
            f'/api/ponds/{self.pond.id}/stocks/',
            {**self.stock_payload, 'batch_name': 'Rohu B'},
            format='json',
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(FishStock.objects.filter(pond=self.pond, species='Rohu').count(), 2)

    def test_create_stock_rejects_duplicate_batch_name_in_same_pond(self):
        self.authenticate()
        self.create_stock()

        response = self.client.post(
            f'/api/ponds/{self.pond.id}/stocks/',
            self.stock_payload,
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('batch_name', response.data)

    def test_user_cannot_access_other_users_stock(self):
        self.authenticate()
        stock = self.create_stock(pond=self.other_pond)

        detail_response = self.client.get(f'/api/stocks/{stock.id}/')
        list_response = self.client.get(f'/api/ponds/{self.other_pond.id}/stocks/')

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(list_response.status_code, 404)

    def test_current_quantity_is_manually_editable(self):
        self.authenticate()
        stock = self.create_stock()

        response = self.client.patch(
            f'/api/stocks/{stock.id}/',
            {'current_quantity': 875},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        stock.refresh_from_db()
        self.assertEqual(stock.current_quantity, 875)

    def test_growth_analysis_includes_optional_feed_fcr(self):
        self.authenticate()
        stock = self.create_stock(current_quantity=900)
        GrowthRecord.objects.create(
            stock=stock,
            recorded_date=date(2026, 1, 31),
            sample_count=25,
            average_weight_g=Decimal('40.00'),
            average_length_cm=Decimal('12.50'),
            mortality_count=5,
            feed_used_kg=Decimal('45.00'),
        )

        response = self.client.get(f'/api/stocks/{stock.id}/')

        self.assertEqual(response.status_code, 200)
        analysis = response.data['growth_analysis']
        self.assertEqual(analysis['days_since_stocking'], 30)
        self.assertEqual(analysis['latest_average_weight_g'], 40.0)
        self.assertEqual(analysis['weight_gain_g'], 30.0)
        self.assertEqual(analysis['estimated_biomass_kg'], 36.0)
        self.assertEqual(analysis['feed_conversion_ratio'], 1.67)
