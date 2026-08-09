from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond
from ponds.views import get_user_pond, user_ponds


User = get_user_model()


class PondQueryUnitTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='pond-query-owner',
            email='pond-query-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='pond-query-other',
            email='pond-query-other@example.com',
            password='StrongPass123!',
        )
        self.staff = User.objects.create_user(
            username='pond-query-staff',
            email='pond-query-staff@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.pond = self.create_pond(self.owner, 'Owner Pond')
        self.other_pond = self.create_pond(self.other_user, 'Other Pond')

    def create_pond(self, owner, name):
        return Pond.objects.create(
            owner=owner,
            name=name,
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def test_user_ponds_returns_only_owned_ponds(self):
        self.assertEqual(list(user_ponds(self.owner)), [self.pond])

    def test_user_ponds_returns_empty_for_user_without_ponds(self):
        user_without_ponds = User.objects.create_user(
            username='pond-query-empty',
            email='pond-query-empty@example.com',
            password='StrongPass123!',
        )

        self.assertEqual(list(user_ponds(user_without_ponds)), [])

    def test_staff_user_ponds_returns_all_ponds(self):
        self.assertCountEqual(user_ponds(self.staff), [self.pond, self.other_pond])

    def test_get_user_pond_returns_owned_pond(self):
        self.assertEqual(get_user_pond(self.owner, self.pond.pk), self.pond)

    def test_get_user_pond_hides_other_users_pond(self):
        self.assertIsNone(get_user_pond(self.owner, self.other_pond.pk))

    def test_get_user_pond_returns_none_for_missing_id(self):
        self.assertIsNone(get_user_pond(self.owner, 999999))
