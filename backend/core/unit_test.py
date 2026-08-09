from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from ponds.models import Pond

from .models import Notification
from .serializers import (
    LoginSerializer,
    NotificationSerializer,
    SignupSerializer,
    UserSerializer,
)
from .services.farm_advisor import (
    build_fallback_advice,
    normalize_list,
    serialize,
)
from .services.gemini import (
    GeminiError,
    extract_text,
    generate_text_response,
    strip_json_code_block,
)


User = get_user_model()


class CoreSerializerUnitTests(TestCase):
    def test_signup_serializer_creates_user_and_splits_full_name(self):
        serializer = SignupSerializer(
            data={
                'full_name': 'Amina Rahman',
                'email': ' AMINA@example.com ',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, 'amina@example.com')
        self.assertEqual(user.first_name, 'Amina')
        self.assertEqual(user.last_name, 'Rahman')
        self.assertTrue(user.check_password('StrongPass123!'))

    def test_signup_serializer_rejects_mismatched_passwords(self):
        serializer = SignupSerializer(
            data={
                'full_name': 'Amina Rahman',
                'email': 'amina@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'DifferentPass123!',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['confirm_password'][0]),
            'Passwords do not match.',
        )

    def test_signup_serializer_rejects_existing_email_case_insensitively(self):
        User.objects.create_user(
            username='existing-user',
            email='owner@example.com',
            password='StrongPass123!',
        )
        serializer = SignupSerializer(
            data={
                'full_name': 'Another Owner',
                'email': 'OWNER@example.com',
                'password': 'StrongPass123!',
                'confirm_password': 'StrongPass123!',
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('already exists', str(serializer.errors['email'][0]))

    def test_login_serializer_accepts_email_and_returns_user(self):
        user = User.objects.create_user(
            username='login-owner',
            email='login@example.com',
            password='StrongPass123!',
        )
        serializer = LoginSerializer(
            data={'email': ' LOGIN@EXAMPLE.COM ', 'password': 'StrongPass123!'}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['user'], user)

    def test_login_serializer_rejects_invalid_credentials(self):
        User.objects.create_user(
            username='login-owner',
            email='login@example.com',
            password='StrongPass123!',
        )
        serializer = LoginSerializer(
            data={'email': 'login@example.com', 'password': 'WrongPass123!'}
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['non_field_errors'][0]),
            'Invalid email or password.',
        )

    def test_user_serializer_uses_default_market_profile(self):
        user = User.objects.create_user(
            username='profile-owner',
            email='profile@example.com',
            password='StrongPass123!',
            first_name='Profile',
            last_name='Owner',
        )

        data = UserSerializer(user).data

        self.assertEqual(data['full_name'], 'Profile Owner')
        self.assertEqual(data['market_profile']['role'], 'both')
        self.assertTrue(data['market_profile']['can_buy'])
        self.assertTrue(data['market_profile']['can_sell'])


class NotificationModelUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notification-owner',
            email='notification-owner@example.com',
            password='StrongPass123!',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='Notification Pond',
            location='Natore',
            area_decimal=Decimal('24.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=2000,
        )

    def test_notification_uses_unread_low_priority_defaults(self):
        notification = Notification.objects.create(
            user=self.user,
            pond=self.pond,
            parameter='pH',
            current_value='5.8',
            reason='pH is below the recommended range.',
        )

        self.assertEqual(notification.priority, Notification.Priority.LOW)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.pond, self.pond)

    def test_notification_string_contains_priority_and_parameter(self):
        notification = Notification.objects.create(
            user=self.user,
            pond=self.pond,
            parameter='Dissolved oxygen',
            current_value='3.2 mg/L',
            reason='Dissolved oxygen is low.',
            priority=Notification.Priority.HIGH,
        )

        self.assertEqual(str(notification), 'High: Dissolved oxygen in Notification Pond')

    def test_notification_serializer_includes_pond_name(self):
        notification = Notification.objects.create(
            user=self.user,
            pond=self.pond,
            parameter='Temperature',
            current_value='34 C',
            reason='Water temperature is high.',
            priority=Notification.Priority.MEDIUM,
        )

        data = NotificationSerializer(notification).data

        self.assertEqual(data['pond'], self.pond.id)
        self.assertEqual(data['pond_name'], 'Notification Pond')
        self.assertEqual(data['priority'], Notification.Priority.MEDIUM)
        self.assertFalse(data['is_read'])


class CoreServiceUnitTests(SimpleTestCase):
    def test_normalize_list_keeps_non_empty_values_as_strings(self):
        self.assertEqual(normalize_list(['  Check water  ', 12, '', None]), ['Check water', '12', 'None'])
        self.assertEqual(normalize_list('not a list'), [])

    def test_serialize_converts_nested_decimal_and_dates(self):
        value = {
            'weight': Decimal('12.50'),
            'date': date(2026, 1, 15),
            'timestamp': datetime(2026, 1, 15, 10, 30),
            'items': [Decimal('2.00')],
        }

        self.assertEqual(
            serialize(value),
            {
                'weight': '12.50',
                'date': '2026-01-15',
                'timestamp': '2026-01-15T10:30:00',
                'items': ['2.00'],
            },
        )

    def test_fallback_advice_reports_missing_water_and_stock(self):
        advice = build_fallback_advice(
            {'water_quality': {}, 'fish_health': {}, 'stock': {'current_quantity': 0}}
        )

        self.assertEqual(advice['source'], 'fallback')
        self.assertEqual(advice['priority'], 'Attention')
        self.assertIn('Water quality data is missing.', advice['risks'])
        self.assertIn('No active stock quantity is available.', advice['risks'])

    def test_strip_json_code_block_removes_markdown_wrapper(self):
        self.assertEqual(strip_json_code_block('```json\n{"ok": true}\n```'), '{"ok": true}')
        self.assertEqual(strip_json_code_block('{"ok": true}'), '{"ok": true}')

    def test_extract_text_joins_gemini_parts(self):
        response = {
            'candidates': [
                {'content': {'parts': [{'text': 'first '}, {'text': 'second'}]}}
            ]
        }

        self.assertEqual(extract_text(response), 'first second')

    def test_extract_text_rejects_missing_candidates(self):
        with self.assertRaisesRegex(GeminiError, 'no candidates'):
            extract_text({'candidates': []})

    @override_settings(GOOGLE_API_KEY='')
    def test_generate_text_response_requires_api_key(self):
        with self.assertRaisesRegex(GeminiError, 'not configured'):
            generate_text_response('Give advice')

    @patch('core.services.farm_advisor.is_gemini_configured', return_value=False)
    def test_gemini_disabled_returns_fallback_advice(self, configured):
        from .services.farm_advisor import get_farm_advice

        context = {
            'water_quality': {},
            'fish_health': {},
            'stock': {'current_quantity': 0},
        }
        with patch('core.services.farm_advisor.build_farm_context', return_value=context):
            advice = get_farm_advice(object())

        self.assertFalse(advice['ai_enabled'])
        self.assertEqual(advice['source'], 'fallback')
        configured.assert_called_once_with()
