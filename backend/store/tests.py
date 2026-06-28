import builtins
import importlib
import sys
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


User = get_user_model()


class SettingsImportTests(SimpleTestCase):
    def test_settings_load_without_python_dotenv_dependency(self):
        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == 'dotenv':
                raise ImportError('dotenv not installed')
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=fake_import):
            sys.modules.pop('backend.settings', None)
            with patch.dict(sys.modules, {'dotenv': None}):
                module = importlib.import_module('backend.settings')

        self.assertTrue(hasattr(module, 'INSTALLED_APPS'))
        self.assertTrue(hasattr(module, 'DATABASES'))


class SignupTests(APITestCase):
    def test_signup_creates_user_account(self):
        payload = {
            'full_name': 'Amina Rahman',
            'email': 'AMINA@example.com',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }

        response = self.client.post('/api/auth/signup/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'amina@example.com')
        self.assertEqual(response.data['user']['first_name'], 'Amina')
        self.assertEqual(response.data['user']['last_name'], 'Rahman')

        user = User.objects.get(email='amina@example.com')
        self.assertTrue(user.check_password(payload['password']))
        self.assertTrue(Token.objects.filter(user=user, key=response.data['token']).exists())

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(
            username='amina',
            email='amina@example.com',
            password='StrongPass123!',
        )

        response = self.client.post(
            '/api/auth/signup/',
            {
                'full_name': 'Amina Rahman',
                'email': 'AMINA@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.filter(email__iexact='amina@example.com').count(), 1)
