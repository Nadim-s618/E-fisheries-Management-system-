from django.contrib.auth import get_user_model
from django.test import TestCase

from core.serializers import (
    LoginSerializer,
    NotificationSerializer,
    SignupSerializer,
    UserSerializer,
)
from core.models import Notification
from ponds.models import Pond


User = get_user_model()


class CoreSerializerUnitTests(TestCase):
    def test_signup_serializer_creates_user_and_splits_full_name(self):
        serializer = SignupSerializer(data={
            'full_name': 'Amina Rahman',
            'email': ' AMINA@example.com ',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, 'amina@example.com')
        self.assertEqual(user.first_name, 'Amina')
        self.assertEqual(user.last_name, 'Rahman')
        self.assertTrue(user.check_password('StrongPass123!'))

    def test_signup_serializer_rejects_mismatched_passwords(self):
        serializer = SignupSerializer(data={
            'full_name': 'Amina Rahman',
            'email': 'amina@example.com',
            'password': 'StrongPass123!',
            'confirm_password': 'DifferentPass123!',
        })

        self.assertFalse(serializer.is_valid())
        self.assertEqual(str(serializer.errors['confirm_password'][0]), 'Passwords do not match.')

    def test_signup_serializer_rejects_existing_email_case_insensitively(self):
        User.objects.create_user(
            username='existing-user',
            email='owner@example.com',
            password='StrongPass123!',
        )
        serializer = SignupSerializer(data={
            'full_name': 'Another Owner',
            'email': 'OWNER@example.com',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn('already exists', str(serializer.errors['email'][0]))

    def test_login_serializer_accepts_email_and_returns_user(self):
        user = User.objects.create_user(
            username='login-owner',
            email='login@example.com',
            password='StrongPass123!',
        )
        serializer = LoginSerializer(data={
            'email': ' LOGIN@EXAMPLE.COM ',
            'password': 'StrongPass123!',
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['user'], user)

    def test_login_serializer_rejects_invalid_credentials(self):
        User.objects.create_user(
            username='login-owner',
            email='login@example.com',
            password='StrongPass123!',
        )
        serializer = LoginSerializer(data={
            'email': 'login@example.com',
            'password': 'WrongPass123!',
        })

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['non_field_errors'][0]),
            'Invalid email or password.',
        )

    def test_user_serializer_uses_default_market_profile(self):
        user = User.objects.create_user(
            username='profile-owner',
            email='profile-owner@example.com',
            password='StrongPass123!',
            first_name='Profile',
            last_name='Owner',
        )

        data = UserSerializer(user).data

        self.assertEqual(data['full_name'], 'Profile Owner')
        self.assertEqual(data['market_profile']['role'], 'both')
        self.assertTrue(data['market_profile']['can_buy'])
        self.assertTrue(data['market_profile']['can_sell'])

    def test_notification_serializer_includes_pond_name(self):
        user = User.objects.create_user(
            username='serializer-owner',
            email='serializer-owner@example.com',
            password='StrongPass123!',
        )
        pond = Pond.objects.create(
            owner=user,
            name='Serializer Pond',
            location='Natore',
            area_decimal='24.00',
            average_depth_ft='5.00',
            stocking_capacity=2000,
        )
        notification = Notification.objects.create(
            user=user,
            pond=pond,
            parameter='Temperature',
            current_value='34 C',
            reason='Water temperature is high.',
        )

        data = NotificationSerializer(notification).data

        self.assertEqual(data['pond'], pond.id)
        self.assertEqual(data['pond_name'], 'Serializer Pond')
