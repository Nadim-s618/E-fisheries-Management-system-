from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ponds.models import Pond

from ..models import FishStock


User = get_user_model()


class FishStockModelUnitTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='stock-model-unit-owner',
            email='stock-model-unit-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=user,
            name='Stock Model Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def test_clean_rejects_invalid_business_values(self):
        stock = FishStock(
            pond=self.pond,
            species=' ',
            batch_name=' ',
            stocking_date=date(2026, 1, 1),
            initial_quantity=0,
            current_quantity=-1,
            initial_average_weight_g=Decimal('0.00'),
        )

        with self.assertRaises(ValidationError) as raised:
            stock.full_clean()

        self.assertEqual(
            set(raised.exception.message_dict),
            {'species', 'batch_name', 'initial_quantity', 'current_quantity', 'initial_average_weight_g'},
        )

    def test_string_representation_contains_batch_and_species(self):
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
