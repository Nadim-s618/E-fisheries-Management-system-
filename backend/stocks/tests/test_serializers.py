from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond

from ..models import FishStock
from ..serializers import FishStockSerializer


User = get_user_model()


class FishStockSerializerUnitTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='stock-serializer-unit-owner',
            email='stock-serializer-unit-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=user,
            name='Stock Serializer Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def valid_data(self, **overrides):
        data = {
            'species': 'Rohu',
            'batch_name': 'Rohu A',
            'stocking_date': date(2026, 1, 1),
            'initial_quantity': 1000,
            'current_quantity': 950,
            'initial_average_weight_g': Decimal('10.00'),
            'status': FishStock.Status.ACTIVE,
        }
        data.update(overrides)
        return data

    def test_serializer_trims_names(self):
        serializer = FishStockSerializer(
            data=self.valid_data(species='  Rohu  ', batch_name='  Rohu B  '),
            context={'pond': self.pond},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['species'], 'Rohu')
        self.assertEqual(serializer.validated_data['batch_name'], 'Rohu B')

    def test_serializer_rejects_non_positive_values(self):
        serializer = FishStockSerializer(
            data=self.valid_data(
                species=' ',
                batch_name=' ',
                initial_quantity=0,
                current_quantity=-1,
                initial_average_weight_g=Decimal('0.00'),
            ),
            context={'pond': self.pond},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(str(serializer.errors['species'][0]), 'This field may not be blank.')
        self.assertEqual(str(serializer.errors['batch_name'][0]), 'This field may not be blank.')
        self.assertEqual(str(serializer.errors['initial_quantity'][0]), 'Initial quantity must be greater than zero.')
        self.assertEqual(str(serializer.errors['current_quantity'][0]), 'Ensure this value is greater than or equal to 0.')
        self.assertEqual(str(serializer.errors['initial_average_weight_g'][0]), 'Initial average weight must be greater than zero.')

    def test_serializer_rejects_duplicate_batch_name_case_insensitively(self):
        FishStock.objects.create(pond=self.pond, **self.valid_data())
        serializer = FishStockSerializer(
            data=self.valid_data(batch_name='rohu a', species='Catla'),
            context={'pond': self.pond},
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['batch_name'][0]),
            'This pond already has a stock batch with this name.',
        )
