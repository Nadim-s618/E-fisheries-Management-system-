from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from market_bridge.models import MarketListing, MarketOrder
from market_bridge.serializers import (
    GuestMarketCartItemSerializer,
    MarketListingSerializer,
    MarketOrderSerializer,
    PublicOrderTrackingSerializer,
)


class MarketBridgeSerializerUnitTests(SimpleTestCase):
    def build_listing(self):
        seller = get_user_model()(username='seller')
        return MarketListing(
            id=4,
            seller=seller,
            species='Rui',
            title='Fresh Rui',
            quantity_kg=Decimal('100.00'),
            available_quantity_kg=Decimal('50.00'),
            unit_price=Decimal('320.00'),
            location='Dhaka',
        )

    def test_listing_serializer_exposes_calculated_total_value(self):
        data = MarketListingSerializer(self.build_listing()).data

        self.assertEqual(data['species'], 'Rui')
        self.assertEqual(data['status'], MarketListing.Status.ACTIVE)
        self.assertEqual(data['total_value'], '16000.00')
        self.assertEqual(data['seller_name'], 'seller')

    def test_listing_serializer_rejects_invalid_numeric_values(self):
        serializer = MarketListingSerializer()

        with self.assertRaisesMessage(Exception, 'Quantity must be greater than zero.'):
            serializer.validate_quantity_kg(Decimal('0'))
        with self.assertRaisesMessage(Exception, 'Unit price must be greater than zero.'):
            serializer.validate_unit_price(Decimal('-1'))

    def test_order_serializer_marks_server_calculated_fields_read_only(self):
        read_only = set(MarketOrderSerializer.Meta.read_only_fields)

        self.assertTrue({'unit_price', 'total_price', 'transaction_code', 'status'}.issubset(read_only))

    def test_public_tracking_serializer_returns_route_status_fields(self):
        listing = self.build_listing()
        order = MarketOrder(
            listing=listing,
            quantity_kg=Decimal('10.00'),
            unit_price=Decimal('320.00'),
            total_price=Decimal('3200.00'),
            transaction_code='MF-12345678',
            status=MarketOrder.Status.SHIPPED,
        )
        data = PublicOrderTrackingSerializer(order).data

        self.assertEqual(data['transaction_code'], 'MF-12345678')
        self.assertEqual(data['listing_title'], 'Fresh Rui')
        self.assertEqual(data['status'], MarketOrder.Status.SHIPPED)
        self.assertEqual(data['status_display'], 'Shipped')

    def test_cart_item_serializer_rejects_zero_quantity(self):
        serializer = GuestMarketCartItemSerializer()

        with self.assertRaisesMessage(Exception, 'Quantity must be greater than zero.'):
            serializer.validate_quantity_kg(Decimal('0'))
