from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from market_bridge.models import MarketListing, MarketOrder


LISTINGS_URL = '/api/market-bridge/listings/'
ORDERS_URL = '/api/market-bridge/orders/'


class MarketBridgeAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(
            username='seller', email='seller@example.com', password='pass',
        )
        self.buyer = user_model.objects.create_user(
            username='buyer', email='buyer@example.com', password='pass',
        )
        self.listing = self.create_listing()

    def create_listing(self, **overrides):
        values = {
            'seller': self.seller,
            'species': 'Rui',
            'title': 'Fresh Rui',
            'quantity_kg': Decimal('100.00'),
            'available_quantity_kg': Decimal('100.00'),
            'unit_price': Decimal('320.00'),
            'location': 'Dhaka',
        }
        values.update(overrides)
        return MarketListing.objects.create(**values)

    def order_payload(self, **overrides):
        payload = {
            'listing': self.listing.id,
            'quantity_kg': '10.00',
            'buyer_full_name': 'Nadim Ahmed',
            'buyer_address': 'House 12, Road 4, Dhaka',
            'buyer_contact_number': '+8801712345678',
            'buyer_note': 'Please call before delivery.',
        }
        payload.update(overrides)
        return payload

    def create_order(self, **overrides):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(ORDERS_URL, self.order_payload(**overrides), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return MarketOrder.objects.get(pk=response.data['id'])

    def test_listing_and_order_endpoints_require_authentication(self):
        self.assertEqual(self.client.get(LISTINGS_URL).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(ORDERS_URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_seller_can_create_listing_with_default_available_quantity(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post(LISTINGS_URL, {
            'species': 'Catla',
            'title': 'Fresh Catla',
            'quantity_kg': '25.00',
            'unit_price': '400.00',
            'location': 'Khulna',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        listing = MarketListing.objects.get(title='Fresh Catla')
        self.assertEqual(listing.available_quantity_kg, Decimal('25.00'))
        self.assertEqual(response.data['seller'], self.seller.id)
        self.assertEqual(response.data['total_value'], '10000.00')

    def test_non_owner_cannot_retrieve_or_update_another_users_listing(self):
        self.client.force_authenticate(self.buyer)

        retrieve_response = self.client.get(f'{LISTINGS_URL}{self.listing.id}/')
        update_response = self.client.patch(
            f'{LISTINGS_URL}{self.listing.id}/', {'title': 'Changed'}, format='json',
        )

        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_order_requires_buyer_contact_details(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(ORDERS_URL, {
            'listing': self.listing.id,
            'quantity_kg': '10.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('buyer_full_name', response.data)
        self.assertIn('buyer_address', response.data)
        self.assertIn('buyer_contact_number', response.data)

    def test_order_saves_buyer_contact_details_and_calculated_fields(self):
        order = self.create_order()

        self.assertEqual(order.buyer, self.buyer)
        self.assertEqual(order.buyer_full_name, 'Nadim Ahmed')
        self.assertEqual(order.buyer_address, 'House 12, Road 4, Dhaka')
        self.assertEqual(order.buyer_contact_number, '+8801712345678')
        self.assertEqual(order.total_price, Decimal('3200.00'))
        self.assertTrue(order.transaction_code.startswith('MF-'))

    def test_seller_accepting_order_reserves_stock_and_marks_sold_out(self):
        order = self.create_order(quantity_kg='100.00')
        self.client.force_authenticate(self.seller)

        response = self.client.post(f'{ORDERS_URL}{order.id}/accept/', {
            'seller_note': 'Order accepted.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.listing.refresh_from_db()
        self.assertEqual(order.status, MarketOrder.Status.ACCEPTED)
        self.assertEqual(order.seller_note, 'Order accepted.')
        self.assertEqual(self.listing.available_quantity_kg, Decimal('0.00'))
        self.assertEqual(self.listing.status, MarketListing.Status.SOLD_OUT)

    def test_buyer_can_cancel_only_a_pending_order(self):
        order = self.create_order()
        self.client.force_authenticate(self.buyer)

        response = self.client.post(f'{ORDERS_URL}{order.id}/cancel/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, MarketOrder.Status.CANCELLED)

        second_response = self.client.post(f'{ORDERS_URL}{order.id}/cancel/')
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)


class PublicMarketStoreAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.store_owner = user_model.objects.create_user(
            username='store-owner', email='shahoriyernadim@gmail.com', password='pass',
        )
        self.other_seller = user_model.objects.create_user(
            username='other-seller', email='other@example.com', password='pass',
        )

    def create_listing(self, seller, **overrides):
        values = {
            'seller': seller,
            'species': 'Rui',
            'title': 'Public Rui',
            'quantity_kg': Decimal('40.00'),
            'available_quantity_kg': Decimal('40.00'),
            'unit_price': Decimal('300.00'),
            'location': 'Dhaka',
        }
        values.update(overrides)
        return MarketListing.objects.create(**values)

    def test_public_store_returns_only_the_configured_store_owners_active_stock(self):
        public_listing = self.create_listing(self.store_owner)
        self.create_listing(self.store_owner, title='Paused Rui', status=MarketListing.Status.PAUSED)
        self.create_listing(self.other_seller, title='Private Rui')

        response = self.client.get('/api/market-bridge/public-store/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [public_listing.id])

    def test_guest_order_can_be_tracked_by_case_insensitive_transaction_code(self):
        listing = self.create_listing(self.store_owner)
        response = self.client.post('/api/market-bridge/public-store/orders/', {
            'listing': listing.id,
            'quantity_kg': '5.00',
            'buyer_full_name': 'Public Buyer',
            'buyer_address': 'Dhaka',
            'buyer_contact_number': '01700000000',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        code = response.data['transaction_code']
        self.assertEqual(response.data['buyer'], None)
        self.assertEqual(response.data['total_price'], '1500.00')

        tracking = self.client.get(f'/api/market-bridge/public-store/track/{code.lower()}/')

        self.assertEqual(tracking.status_code, status.HTTP_200_OK)
        self.assertEqual(tracking.data['transaction_code'], code)
        self.assertEqual(tracking.data['orders'][0]['status'], MarketOrder.Status.PENDING)

    def test_tracking_returns_not_found_for_unknown_transaction_code(self):
        response = self.client.get('/api/market-bridge/public-store/track/MF-UNKNOWN/')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('transaction_code', response.data)
