from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import MarketListing, MarketOrder


class MarketOrderContactDetailsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user(username='seller', password='pass')
        self.buyer = User.objects.create_user(username='buyer', password='pass')
        self.listing = MarketListing.objects.create(
            seller=self.seller,
            species='Rui',
            title='Fresh Rui',
            quantity_kg=Decimal('100.00'),
            available_quantity_kg=Decimal('100.00'),
            unit_price=Decimal('320.00'),
            location='Dhaka',
        )
        self.client.force_authenticate(self.buyer)

    def test_order_requires_buyer_contact_details(self):
        response = self.client.post('/api/market-bridge/orders/', {
            'listing': self.listing.id,
            'quantity_kg': '10.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('buyer_full_name', response.data)
        self.assertIn('buyer_address', response.data)
        self.assertIn('buyer_contact_number', response.data)

    def test_order_saves_buyer_contact_details(self):
        response = self.client.post('/api/market-bridge/orders/', {
            'listing': self.listing.id,
            'quantity_kg': '10.00',
            'buyer_full_name': 'Nadim Ahmed',
            'buyer_address': 'House 12, Road 4, Dhaka',
            'buyer_contact_number': '+8801712345678',
            'buyer_note': 'Please call before delivery.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = MarketOrder.objects.get()
        self.assertEqual(order.buyer_full_name, 'Nadim Ahmed')
        self.assertEqual(order.buyer_address, 'House 12, Road 4, Dhaka')
        self.assertEqual(order.buyer_contact_number, '+8801712345678')
