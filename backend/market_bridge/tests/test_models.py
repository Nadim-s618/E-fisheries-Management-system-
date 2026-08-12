from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from market_bridge.models import MarketListing, MarketOrder, MarketProfile, make_transaction_code


class MarketBridgeModelUnitTests(SimpleTestCase):
    def build_listing(self, **overrides):
        values = {
            'species': 'Rui',
            'title': 'Fresh Rui',
            'quantity_kg': Decimal('100.00'),
            'available_quantity_kg': Decimal('60.00'),
            'unit_price': Decimal('320.00'),
            'location': 'Dhaka',
        }
        values.update(overrides)
        return MarketListing(**values)

    def test_transaction_code_has_expected_prefix_and_length(self):
        code = make_transaction_code()

        self.assertTrue(code.startswith('MF-'))
        self.assertEqual(len(code), 11)

    def test_listing_total_value_multiplies_available_stock_by_unit_price(self):
        listing = self.build_listing()

        self.assertEqual(listing.total_value, Decimal('19200.0000'))
        self.assertEqual(str(listing), 'Fresh Rui')

    def test_listing_clean_rejects_available_quantity_above_listed_quantity(self):
        listing = self.build_listing(available_quantity_kg=Decimal('101.00'))

        with self.assertRaises(ValidationError) as raised:
            listing.clean()

        self.assertIn('available_quantity_kg', raised.exception.message_dict)

    def test_listing_clean_rejects_inventory_without_stock(self):
        listing = self.build_listing(source_type=MarketListing.SourceType.INVENTORY)

        with self.assertRaises(ValidationError) as raised:
            listing.clean()

        self.assertIn('fish_stock', raised.exception.message_dict)

    def test_order_clean_rejects_empty_buyer_details(self):
        order = MarketOrder(
            quantity_kg=Decimal('10.00'),
            unit_price=Decimal('320.00'),
            total_price=Decimal('3200.00'),
            buyer_full_name='',
            buyer_address='',
            buyer_contact_number='',
        )

        with self.assertRaises(ValidationError) as raised:
            order.clean()

        self.assertEqual(
            set(raised.exception.message_dict),
            {'buyer_full_name', 'buyer_address', 'buyer_contact_number'},
        )

    def test_profile_permissions_are_available_for_buyer_and_seller(self):
        profile = MarketProfile()

        self.assertTrue(profile.can_buy)
        self.assertTrue(profile.can_sell)
