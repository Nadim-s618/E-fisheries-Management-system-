from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from growth.models import GrowthRecord
from ponds.models import Pond

from .models import FishStock
from .serializers import FishStockSerializer


User = get_user_model()


class FishStockModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='stock-model-owner',
            email='stock-model-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='Model Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def test_stock_requires_valid_business_fields(self):
        stock = FishStock(
            pond=self.pond,
            species=' ',
            batch_name=' ',
            stocking_date=date(2026, 1, 1),
            initial_quantity=0,
            current_quantity=-1,
            initial_average_weight_g=Decimal('0.00'),
        )

        with self.assertRaises(ValidationError) as context:
            stock.full_clean()

        errors = context.exception.message_dict
        self.assertIn('species', errors)
        self.assertIn('batch_name', errors)
        self.assertIn('initial_quantity', errors)
        self.assertIn('current_quantity', errors)
        self.assertIn('initial_average_weight_g', errors)

    def test_stock_string_contains_batch_and_species(self):
        stock = FishStock(
            pond=self.pond,
            species='Rohu',
            batch_name='Rohu A',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=950,
            initial_average_weight_g=Decimal('10.00'),
        )

        self.assertEqual(str(stock), 'Rohu A - Rohu')


class FishStockSerializerTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='stock-serializer-owner',
            email='stock-serializer-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='Serializer Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def create_stock(self, **overrides):
        data = {
            'pond': self.pond,
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

    def test_serializer_trims_species_and_batch_name(self):
        serializer = FishStockSerializer(
            data={
                'species': '  Rohu  ',
                'batch_name': '  Rohu B  ',
                'stocking_date': '2026-01-01',
                'initial_quantity': 1000,
                'current_quantity': 950,
                'initial_average_weight_g': '10.00',
                'status': FishStock.Status.ACTIVE,
            },
            context={'pond': self.pond},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['species'], 'Rohu')
        self.assertEqual(serializer.validated_data['batch_name'], 'Rohu B')

    def test_serializer_rejects_case_insensitive_duplicate_batch_name(self):
        self.create_stock(batch_name='Rohu A')
        serializer = FishStockSerializer(
            data={
                'species': 'Catla',
                'batch_name': 'rohu a',
                'stocking_date': '2026-02-01',
                'initial_quantity': 700,
                'current_quantity': 700,
                'initial_average_weight_g': '12.50',
                'status': FishStock.Status.ACTIVE,
            },
            context={'pond': self.pond},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('batch_name', serializer.errors)

    @patch('stocks.serializers.timezone.localdate', return_value=date(2026, 1, 11))
    def test_growth_analysis_uses_initial_stock_when_no_growth_records(self, localdate):
        stock = self.create_stock(
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=900,
            initial_average_weight_g=Decimal('10.00'),
        )

        data = FishStockSerializer(stock).data

        self.assertEqual(data['growth_analysis']['days_since_stocking'], 10)
        self.assertIsNone(data['growth_analysis']['latest_recorded_date'])
        self.assertEqual(data['growth_analysis']['latest_average_weight_g'], 10.0)
        self.assertEqual(data['growth_analysis']['weight_gain_g'], 0.0)
        self.assertEqual(data['growth_analysis']['daily_growth_rate_g'], 0.0)
        self.assertEqual(data['growth_analysis']['estimated_biomass_kg'], 9.0)
        self.assertEqual(data['growth_analysis']['survival_rate_percent'], 90.0)
        self.assertIsNone(data['growth_analysis']['total_feed_used_kg'])
        self.assertIsNone(data['growth_analysis']['feed_conversion_ratio'])
        self.assertEqual(data['growth_analysis']['growth_records_count'], 0)
        localdate.assert_called_once()


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

    def test_stock_detail_requires_authentication(self):
        stock = self.create_stock()

        response = self.client.get(f'/api/stocks/{stock.id}/')

        self.assertEqual(response.status_code, 401)

    def test_create_stock_assigns_url_pond(self):
        self.authenticate()

        response = self.client.post(
            f'/api/ponds/{self.pond.id}/stocks/',
            {**self.stock_payload, 'pond': self.other_pond.id},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        stock = FishStock.objects.get(pk=response.data['id'])
        self.assertEqual(stock.pond, self.pond)
        self.assertEqual(response.data['pond']['id'], self.pond.id)
        self.assertEqual(response.data['status_display'], 'Active')

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

    def test_create_stock_allows_same_batch_name_in_different_ponds(self):
        self.authenticate()
        self.create_stock()
        second_pond = Pond.objects.create(
            owner=self.user,
            name='South Pond',
            location='Natore',
            area_decimal=Decimal('20.00'),
            average_depth_ft=Decimal('4.50'),
            stocking_capacity=1500,
        )

        response = self.client.post(
            f'/api/ponds/{second_pond.id}/stocks/',
            self.stock_payload,
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(FishStock.objects.filter(batch_name='Rohu A').count(), 2)

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

    def test_create_stock_rejects_invalid_stock_values(self):
        self.authenticate()

        response = self.client.post(
            f'/api/ponds/{self.pond.id}/stocks/',
            {
                **self.stock_payload,
                'species': ' ',
                'batch_name': ' ',
                'initial_quantity': 0,
                'current_quantity': -1,
                'initial_average_weight_g': '0.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('species', response.data)
        self.assertIn('batch_name', response.data)
        self.assertIn('initial_quantity', response.data)
        self.assertIn('current_quantity', response.data)
        self.assertIn('initial_average_weight_g', response.data)

    def test_user_only_lists_stocks_for_requested_owned_pond(self):
        self.authenticate()
        own_stock = self.create_stock()
        self.create_stock(batch_name='Catla A', species='Catla')
        self.create_stock(pond=self.other_pond, batch_name='Other Batch')

        response = self.client.get(f'/api/ponds/{self.pond.id}/stocks/')

        self.assertEqual(response.status_code, 200)
        response_ids = {stock['id'] for stock in response.data}
        pond_stock_ids = set(
            FishStock.objects.filter(pond=self.pond).values_list('id', flat=True)
        )
        self.assertIn(own_stock.id, response_ids)
        self.assertEqual(response_ids, pond_stock_ids)

    def test_staff_can_list_stocks_for_any_pond(self):
        staff_user = User.objects.create_user(
            username='stock-manager',
            email='stock-manager@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        stock = self.create_stock(pond=self.other_pond)
        self.authenticate(staff_user)

        response = self.client.get(f'/api/ponds/{self.other_pond.id}/stocks/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], stock.id)

    def test_user_cannot_access_other_users_stock(self):
        self.authenticate()
        stock = self.create_stock(pond=self.other_pond)

        detail_response = self.client.get(f'/api/stocks/{stock.id}/')
        list_response = self.client.get(f'/api/ponds/{self.other_pond.id}/stocks/')

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(list_response.status_code, 404)

    def test_retrieve_stock_returns_nested_pond_and_growth_records(self):
        self.authenticate()
        stock = self.create_stock()
        GrowthRecord.objects.create(
            stock=stock,
            recorded_date=date(2026, 1, 31),
            sample_count=25,
            average_weight_g=Decimal('40.00'),
        )

        response = self.client.get(f'/api/stocks/{stock.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], stock.id)
        self.assertEqual(response.data['pond']['id'], self.pond.id)
        self.assertEqual(response.data['status_display'], 'Active')
        self.assertEqual(len(response.data['growth_records']), 1)

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

    def test_update_stock_changes_status_and_notes(self):
        self.authenticate()
        stock = self.create_stock(notes='Old note.')

        response = self.client.patch(
            f'/api/stocks/{stock.id}/',
            {
                'status': FishStock.Status.PARTIAL_HARVEST,
                'notes': 'Partial harvest completed.',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        stock.refresh_from_db()
        self.assertEqual(stock.status, FishStock.Status.PARTIAL_HARVEST)
        self.assertEqual(stock.notes, 'Partial harvest completed.')

    def test_update_stock_rejects_negative_current_quantity(self):
        self.authenticate()
        stock = self.create_stock()

        response = self.client.patch(
            f'/api/stocks/{stock.id}/',
            {'current_quantity': -1},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('current_quantity', response.data)
        stock.refresh_from_db()
        self.assertEqual(stock.current_quantity, 950)

    def test_update_stock_rejects_duplicate_batch_name_in_same_pond(self):
        self.authenticate()
        first_stock = self.create_stock(batch_name='Rohu A')
        stock = self.create_stock(batch_name='Catla A', species='Catla')

        response = self.client.patch(
            f'/api/stocks/{stock.id}/',
            {'batch_name': first_stock.batch_name},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('batch_name', response.data)

    def test_delete_stock_removes_it(self):
        self.authenticate()
        stock = self.create_stock()

        response = self.client.delete(f'/api/stocks/{stock.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(FishStock.objects.filter(pk=stock.pk).exists())

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
