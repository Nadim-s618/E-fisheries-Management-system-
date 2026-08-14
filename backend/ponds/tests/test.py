from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from ponds.models import Pond
from water_quality.models import WaterQualityReading


User = get_user_model()


class PondModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pond-owner',
            email='pond-owner@example.com',
            password='StrongPass123!',
        )

    def test_pond_requires_positive_measurements(self):
        pond = Pond(
            owner=self.user,
            name='North Pond',
            location='Madhnagar',
            area_decimal=Decimal('0.00'),
            average_depth_ft=Decimal('-1.00'),
            stocking_capacity=0,
        )

        with self.assertRaises(ValidationError) as context:
            pond.full_clean()

        self.assertIn('area_decimal', context.exception.message_dict)
        self.assertIn('average_depth_ft', context.exception.message_dict)
        self.assertIn('stocking_capacity', context.exception.message_dict)


class PondApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='amina',
            email='amina@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='karim',
            email='karim@example.com',
            password='StrongPass123!',
        )
        self.staff_user = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='StrongPass123!',
            is_staff=True,
        )
        self.payload = {
            'name': 'Purba Madhnagar',
            'location': 'Natore',
            'area_decimal': '42.50',
            'average_depth_ft': '6.25',
            'water_source': 'mixed',
            'stocking_capacity': 2500,
            'status': 'active',
            'notes': 'Primary grow-out pond.',
        }

    def authenticate(self, user=None):
        self.client.force_authenticate(user=user or self.user)

    def create_pond(self, owner=None, **overrides):
        data = {
            'owner': owner or self.user,
            'name': 'Dighi',
            'location': 'Natore',
            'area_decimal': Decimal('30.00'),
            'average_depth_ft': Decimal('5.50'),
            'water_source': Pond.WaterSource.MIXED,
            'stocking_capacity': 1800,
            'status': Pond.Status.ACTIVE,
        }
        data.update(overrides)
        return Pond.objects.create(**data)

    def test_pond_list_requires_authentication(self):
        response = self.client.get('/api/ponds/')
        self.assertEqual(response.status_code, 401)

    def test_create_pond_assigns_current_user(self):
        self.authenticate()
        response = self.client.post('/api/ponds/', self.payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Purba Madhnagar')
        self.assertEqual(response.data['owner']['email'], 'amina@example.com')
        self.assertTrue(Pond.objects.filter(owner=self.user, name='Purba Madhnagar').exists())

    def test_create_pond_rejects_invalid_measurements(self):
        self.authenticate()
        response = self.client.post('/api/ponds/', {
            **self.payload,
            'area_decimal': '0.00',
            'average_depth_ft': '-2.00',
            'stocking_capacity': 0,
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('area_decimal', response.data)
        self.assertIn('average_depth_ft', response.data)
        self.assertIn('stocking_capacity', response.data)

    def test_create_pond_rejects_duplicate_name_for_same_owner(self):
        self.authenticate()
        self.create_pond(name='Purba Madhnagar')

        response = self.client.post('/api/ponds/', self.payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.data)

    def test_user_only_lists_own_ponds(self):
        self.authenticate()
        own_pond = self.create_pond(name='Own Pond')
        self.create_pond(owner=self.other_user, name='Other Pond')

        response = self.client.get('/api/ponds/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], own_pond.id)

    def test_staff_lists_all_ponds(self):
        self.authenticate(self.staff_user)
        self.create_pond(owner=self.user, name='Owner Pond')
        self.create_pond(owner=self.other_user, name='Other Pond')

        response = self.client.get('/api/ponds/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_user_cannot_access_another_users_pond(self):
        self.authenticate()
        other_pond = self.create_pond(owner=self.other_user, name='Other Pond')

        response = self.client.get(f'/api/ponds/{other_pond.id}/')
        self.assertEqual(response.status_code, 404)

    def test_update_pond(self):
        self.authenticate()
        pond = self.create_pond(name='Old Name')

        response = self.client.patch(
            f'/api/ponds/{pond.id}/',
            {'name': 'Updated Pond', 'status': 'maintenance'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        pond.refresh_from_db()
        self.assertEqual(pond.name, 'Updated Pond')
        self.assertEqual(pond.status, Pond.Status.MAINTENANCE)

    def test_delete_pond(self):
        self.authenticate()
        pond = self.create_pond()

        response = self.client.delete(f'/api/ponds/{pond.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Pond.objects.filter(pk=pond.pk).exists())

    def test_delete_pond_removes_water_quality_readings(self):
        self.authenticate()
        pond = self.create_pond()
        WaterQualityReading.objects.create(
            pond=pond,
            temperature=28,
            ph=7.5,
            dissolved_oxygen=6,
            ammonia=0.1,
            nitrite=0.05,
            nitrate=10,
            turbidity=3,
            water_level=5,
        )

        response = self.client.delete(f'/api/ponds/{pond.id}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Pond.objects.filter(pk=pond.pk).exists())
        self.assertFalse(WaterQualityReading.objects.filter(pond_id=pond.pk).exists())
