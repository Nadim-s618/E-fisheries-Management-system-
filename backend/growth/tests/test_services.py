from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond
from stocks.models import FishStock

from ..models import GrowthRecord
from ..views import get_user_growth_record, user_growth_records


User = get_user_model()


class GrowthServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='growth-service-owner',
            email='growth-service-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='growth-service-other',
            email='growth-service-other@example.com',
            password='StrongPass123!',
        )
        pond = Pond.objects.create(
            owner=self.owner,
            name='Service Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )
        stock = FishStock.objects.create(
            pond=pond,
            species='Rohu',
            batch_name='Service Batch',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=950,
            initial_average_weight_g=Decimal('10.00'),
            status=FishStock.Status.ACTIVE,
        )
        self.record = GrowthRecord.objects.create(
            stock=stock,
            recorded_date=date(2026, 1, 15),
            sample_count=20,
            average_weight_g=Decimal('12.50'),
        )

    def test_user_growth_records_only_returns_records_owned_by_user(self):
        records = user_growth_records(self.owner)

        self.assertEqual(list(records), [self.record])
        self.assertEqual(user_growth_records(self.other_user).count(), 0)

    def test_staff_user_can_access_all_growth_records(self):
        staff = User.objects.create_user(
            username='growth-service-staff',
            email='growth-service-staff@example.com',
            password='StrongPass123!',
            is_staff=True,
        )

        self.assertEqual(list(user_growth_records(staff)), [self.record])

    def test_get_user_growth_record_returns_record_or_none(self):
        self.assertEqual(get_user_growth_record(self.owner, self.record.pk), self.record)
        self.assertIsNone(get_user_growth_record(self.other_user, self.record.pk))
        self.assertIsNone(get_user_growth_record(self.owner, 999999))
