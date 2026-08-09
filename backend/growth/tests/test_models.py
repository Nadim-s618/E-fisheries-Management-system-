from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ponds.models import Pond
from stocks.models import FishStock

from ..models import GrowthRecord


User = get_user_model()


class GrowthRecordModelTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='growth-model-owner',
            email='growth-model-owner@example.com',
            password='StrongPass123!',
        )
        pond = Pond.objects.create(
            owner=user,
            name='Model Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )
        self.stock = FishStock.objects.create(
            pond=pond,
            species='Rohu',
            batch_name='Model Batch',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=950,
            initial_average_weight_g=Decimal('10.00'),
            status=FishStock.Status.ACTIVE,
        )

    def test_clean_rejects_growth_date_before_stocking(self):
        record = GrowthRecord(
            stock=self.stock,
            recorded_date=date(2025, 12, 31),
            sample_count=20,
            average_weight_g=Decimal('12.50'),
        )

        with self.assertRaises(ValidationError) as raised:
            record.full_clean()

        self.assertIn('recorded_date', raised.exception.message_dict)

    def test_clean_rejects_non_positive_growth_values(self):
        record = GrowthRecord(
            stock=self.stock,
            recorded_date=date(2026, 1, 15),
            sample_count=0,
            average_weight_g=Decimal('0.00'),
            average_length_cm=Decimal('-1.00'),
            mortality_count=-1,
            feed_used_kg=Decimal('0.00'),
        )

        with self.assertRaises(ValidationError) as raised:
            record.full_clean()

        self.assertEqual(
            set(raised.exception.message_dict),
            {'sample_count', 'average_weight_g', 'average_length_cm', 'mortality_count', 'feed_used_kg'},
        )

    def test_string_representation_contains_stock_and_date(self):
        record = GrowthRecord(
            stock=self.stock,
            recorded_date=date(2026, 1, 15),
            sample_count=20,
            average_weight_g=Decimal('12.50'),
        )

        self.assertEqual(str(record), 'Model Batch - Rohu growth on 2026-01-15')
