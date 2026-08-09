from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond

from ..models import FishStock
from ..views import get_user_stock, user_stocks


User = get_user_model()


class StockServiceUnitTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='stock-service-owner',
            email='stock-service-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='stock-service-other',
            email='stock-service-other@example.com',
            password='StrongPass123!',
        )
        pond = Pond.objects.create(
            owner=self.owner,
            name='Stock Service Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )
        self.stock = FishStock.objects.create(
            pond=pond,
            species='Rohu',
            batch_name='Service Batch',
            stocking_date=date(2026, 1, 1),
            initial_quantity=1000,
            current_quantity=950,
            initial_average_weight_g=Decimal('10.00'),
            status=FishStock.Status.ACTIVE,
        )

    def test_user_stocks_only_returns_owned_records(self):
        self.assertEqual(list(user_stocks(self.owner)), [self.stock])
        self.assertEqual(user_stocks(self.other_user).count(), 0)

    def test_staff_user_can_access_all_stock_records(self):
        staff = User.objects.create_user(
            username='stock-service-staff',
            email='stock-service-staff@example.com',
            password='StrongPass123!',
            is_staff=True,
        )

        self.assertEqual(list(user_stocks(staff)), [self.stock])

    def test_get_user_stock_returns_record_or_none(self):
        self.assertEqual(get_user_stock(self.owner, self.stock.pk), self.stock)
        self.assertIsNone(get_user_stock(self.other_user, self.stock.pk))
        self.assertIsNone(get_user_stock(self.owner, 999999))
