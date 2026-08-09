from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond
from water_quality.models import WaterQualityReading
from water_quality.serializers import WaterQualityReadingSerializer


User = get_user_model()


class WaterQualityReadingSerializerUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='water-serializer-owner',
            email='water-serializer-owner@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='water-serializer-other',
            email='water-serializer-other@example.com',
            password='StrongPass123!',
        )
        self.pond = self.create_pond(self.user, 'North Pond')
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

    def valid_data(self, **overrides):
        data = {
            'pond': self.pond.id,
            'temperature': 28,
            'ph': 7.2,
            'dissolved_oxygen': 6.5,
            'ammonia': 0.01,
            'nitrite': 0.1,
            'nitrate': 25,
            'turbidity': 55,
            'salinity': 5,
            'water_level': 4.5,
            'overall_status': WaterQualityReading.OverallStatus.GOOD,
        }
        data.update(overrides)
        return data

    def request_context(self, user=None):
        request = type('Request', (), {
            'user': user or self.user,
        })()
        return {'request': request}

    def test_serializer_accepts_valid_reading(self):
        serializer = WaterQualityReadingSerializer(
            data=self.valid_data(),
            context=self.request_context(),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['pond'], self.pond)
        self.assertEqual(serializer.validated_data['ph'], 7.2)

    def test_serializer_rejects_values_below_allowed_range(self):
        serializer = WaterQualityReadingSerializer(
            data=self.valid_data(ph=-1),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('ph', serializer.errors)

    def test_serializer_rejects_values_above_allowed_range(self):
        serializer = WaterQualityReadingSerializer(
            data=self.valid_data(temperature=51),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('temperature', serializer.errors)

    def test_serializer_allows_missing_optional_salinity(self):
        serializer = WaterQualityReadingSerializer(
            data=self.valid_data(salinity=None),
            context=self.request_context(),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsNone(serializer.validated_data['salinity'])

    def test_non_staff_user_cannot_select_another_users_pond(self):
        serializer = WaterQualityReadingSerializer(
            data=self.valid_data(pond=self.other_pond.id),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('pond', serializer.errors)

    def test_serializer_returns_pond_name_for_saved_reading(self):
        reading_data = self.valid_data()
        reading_data.pop('pond')
        reading = WaterQualityReading.objects.create(
            pond=self.pond,
            **reading_data,
        )

        data = WaterQualityReadingSerializer(reading).data

        self.assertEqual(data['pond_name'], 'North Pond')
        self.assertEqual(data['overall_status'], WaterQualityReading.OverallStatus.GOOD)
