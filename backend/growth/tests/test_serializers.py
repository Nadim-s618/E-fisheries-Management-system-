from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond
from stocks.models import FishStock

from ..models import GrowthRecord
from ..serializers import GrowthRecordSerializer


User = get_user_model()


class GrowthRecordSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='growth-serializer-owner',
            email='growth-serializer-owner@example.com',
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
        self.stock = FishStock.objects.create(
            pond=self.pond,
            species='Rohu',
            batch_name='Serializer Batch',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=950,
            initial_average_weight_g=Decimal('10.00'),
            status=FishStock.Status.ACTIVE,
        )

    def serializer(self, data, instance=None):
        return GrowthRecordSerializer(
            instance=instance,
            data=data,
            context={'stock': self.stock},
        )

    def test_valid_growth_data_is_accepted(self):
        serializer = self.serializer(
            {
                'recorded_date': date(2026, 1, 15),
                'sample_count': 20,
                'average_weight_g': Decimal('12.50'),
                'average_length_cm': Decimal('8.25'),
                'mortality_count': 2,
                'feed_used_kg': Decimal('4.50'),
                'notes': 'Healthy sample.',
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['sample_count'], 20)

    def test_non_positive_measurements_are_rejected(self):
        serializer = self.serializer(
            {
                'recorded_date': date(2026, 1, 15),
                'sample_count': 0,
                'average_weight_g': Decimal('-1.00'),
                'average_length_cm': Decimal('0.00'),
                'mortality_count': -1,
                'feed_used_kg': Decimal('0.00'),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(str(serializer.errors['sample_count'][0]), 'Sample count must be greater than zero.')
        self.assertEqual(str(serializer.errors['average_weight_g'][0]), 'Average weight must be greater than zero.')
        self.assertEqual(str(serializer.errors['average_length_cm'][0]), 'Average length must be greater than zero.')
        self.assertEqual(str(serializer.errors['mortality_count'][0]), 'Ensure this value is greater than or equal to 0.')
        self.assertEqual(str(serializer.errors['feed_used_kg'][0]), 'Feed used must be greater than zero.')

    def test_date_before_stocking_date_is_rejected(self):
        serializer = self.serializer(
            {
                'recorded_date': date(2025, 12, 31),
                'sample_count': 20,
                'average_weight_g': Decimal('12.50'),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(str(serializer.errors['recorded_date'][0]), 'Growth date cannot be before the stocking date.')

    def test_duplicate_date_for_same_stock_is_rejected(self):
        GrowthRecord.objects.create(
            stock=self.stock,
            recorded_date=date(2026, 1, 15),
            sample_count=20,
            average_weight_g=Decimal('12.50'),
        )

        serializer = self.serializer(
            {
                'recorded_date': date(2026, 1, 15),
                'sample_count': 25,
                'average_weight_g': Decimal('13.00'),
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(str(serializer.errors['recorded_date'][0]), 'This stock already has a growth record for this date.')
