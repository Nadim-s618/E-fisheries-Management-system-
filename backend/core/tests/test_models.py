from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from ponds.models import Pond

from core.models import Notification


User = get_user_model()


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
