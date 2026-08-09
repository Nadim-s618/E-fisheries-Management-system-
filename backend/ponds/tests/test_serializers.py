from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond
from ponds.serializers import PondSerializer


User = get_user_model()


class PondSerializerUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pond-serializer-owner',
            email='pond-serializer-owner@example.com',
            password='StrongPass123!',
        )

    def valid_data(self, **overrides):
        data = {
            'name': 'North Pond',
            'location': 'Natore',
            'area_decimal': Decimal('24.00'),
            'average_depth_ft': Decimal('5.00'),
            'water_source': Pond.WaterSource.MIXED,
            'stocking_capacity': 2000,
            'status': Pond.Status.ACTIVE,
        }
        data.update(overrides)
        return data

    def request_context(self):
        request = type('Request', (), {'user': self.user})()
        return {'request': request}

    def test_serializer_accepts_valid_pond_data(self):
        serializer = PondSerializer(
            data=self.valid_data(),
            context=self.request_context(),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['name'], 'North Pond')
        self.assertEqual(serializer.validated_data['area_decimal'], Decimal('24.00'))
        self.assertEqual(serializer.validated_data['stocking_capacity'], 2000)

    def test_serializer_trims_name_and_location(self):
        serializer = PondSerializer(
            data=self.valid_data(name='  North Pond  ', location='  Natore  '),
            context=self.request_context(),
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['name'], 'North Pond')
        self.assertEqual(serializer.validated_data['location'], 'Natore')

    def test_serializer_rejects_blank_name_and_location(self):
        serializer = PondSerializer(
            data=self.valid_data(name=' ', location=' '),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('location', serializer.errors)

    def test_serializer_rejects_non_positive_measurements(self):
        serializer = PondSerializer(
            data=self.valid_data(
                area_decimal=Decimal('0.00'),
                average_depth_ft=Decimal('-1.00'),
                stocking_capacity=0,
            ),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('area_decimal', serializer.errors)
        self.assertIn('average_depth_ft', serializer.errors)
        self.assertIn('stocking_capacity', serializer.errors)

    def test_serializer_rejects_invalid_water_source(self):
        serializer = PondSerializer(
            data=self.valid_data(water_source='well water'),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('water_source', serializer.errors)

    def test_serializer_rejects_duplicate_name_case_insensitively(self):
        Pond.objects.create(owner=self.user, **self.valid_data())
        serializer = PondSerializer(
            data=self.valid_data(name='north pond'),
            context=self.request_context(),
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_serializer_includes_display_fields(self):
        pond = Pond.objects.create(owner=self.user, **self.valid_data())

        data = PondSerializer(pond).data

        self.assertEqual(data['water_source_display'], 'Mixed')
        self.assertEqual(data['status_display'], 'Active')
        self.assertEqual(data['owner']['email'], self.user.email)
