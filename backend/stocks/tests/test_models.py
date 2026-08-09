"""
Pure unit tests for store.models.FishStock.

These tests instantiate FishStock in memory only — no database hits,
no .clean()/.full_clean() validation calls, no .save() calls.
"""
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from ..models import FishStock


def make_stock(**overrides):
    defaults = {
        'pond': MagicMock(name='Pond A'),
        'species': 'Tilapia',
        'batch_name': 'Batch-001',
        'stocking_date': '2026-01-01',
        'initial_quantity': 1000,
        'current_quantity': 1000,
        'initial_average_weight_g': Decimal('12.50'),
    }
    defaults.update(overrides)
    return FishStock(**defaults)


class FishStockStrTests(SimpleTestCase):
    def test_str_returns_batch_name_and_species(self):
        stock = make_stock(batch_name='B-42', species='Catfish')
        self.assertEqual(str(stock), 'B-42 - Catfish')

    def test_str_reflects_updated_fields(self):
        stock = make_stock(batch_name='B-1', species='Tilapia')
        stock.batch_name = 'B-2'
        stock.species = 'Pangasius'
        self.assertEqual(str(stock), 'B-2 - Pangasius')


class FishStockDefaultsTests(SimpleTestCase):
    def test_default_status_is_active(self):
        stock = make_stock()
        self.assertEqual(stock.status, FishStock.Status.ACTIVE)

    def test_notes_defaults_to_empty_string(self):
        stock = FishStock(
            pond=MagicMock(),
            species='Tilapia',
            batch_name='B-1',
            stocking_date='2026-01-01',
            initial_quantity=100,
            current_quantity=100,
            initial_average_weight_g=Decimal('10.00'),
        )
        self.assertEqual(stock.notes, '')


class FishStockStatusChoicesTests(SimpleTestCase):
    def test_status_choices_values(self):
        self.assertEqual(FishStock.Status.ACTIVE, 'active')
        self.assertEqual(FishStock.Status.PARTIAL_HARVEST, 'partial_harvest')
        self.assertEqual(FishStock.Status.HARVESTED, 'harvested')

    def test_status_choices_labels(self):
        self.assertEqual(FishStock.Status.ACTIVE.label, 'Active')
        self.assertEqual(FishStock.Status.PARTIAL_HARVEST.label, 'Partial harvest')
        self.assertEqual(FishStock.Status.HARVESTED.label, 'Harvested')

    def test_status_can_be_assigned_from_choices(self):
        stock = make_stock(status=FishStock.Status.PARTIAL_HARVEST)
        self.assertEqual(stock.status, 'partial_harvest')


class FishStockMetaTests(SimpleTestCase):
    def test_app_label(self):
        self.assertEqual(FishStock._meta.app_label, 'store')

    def test_ordering(self):
        self.assertEqual(
            FishStock._meta.ordering,
            ['pond__name', '-stocking_date', 'species'],
        )

    def test_field_max_lengths(self):
        self.assertEqual(FishStock._meta.get_field('species').max_length, 120)
        self.assertEqual(FishStock._meta.get_field('batch_name').max_length, 120)
        self.assertEqual(FishStock._meta.get_field('status').max_length, 20)

    def test_decimal_field_precision(self):
        field = FishStock._meta.get_field('initial_average_weight_g')
        self.assertEqual(field.max_digits, 8)
        self.assertEqual(field.decimal_places, 2)

    def test_notes_field_is_blankable(self):
        self.assertTrue(FishStock._meta.get_field('notes').blank)

    def test_constraint_names_present(self):
        constraint_names = {c.name for c in FishStock._meta.constraints}
        self.assertEqual(
            constraint_names,
            {
                'unique_stock_batch_name_per_pond',
                'stock_initial_quantity_positive',
                'stock_current_quantity_not_negative',
                'stock_initial_average_weight_positive',
            },
        )


class FishStockFieldAssignmentTests(SimpleTestCase):
    def test_fields_are_set_as_passed(self):
        stock = make_stock(
            species='Rui',
            batch_name='B-99',
            initial_quantity=500,
            current_quantity=480,
            initial_average_weight_g=Decimal('9.75'),
        )
        self.assertEqual(stock.species, 'Rui')
        self.assertEqual(stock.batch_name, 'B-99')
        self.assertEqual(stock.initial_quantity, 500)
        self.assertEqual(stock.current_quantity, 480)
        self.assertEqual(stock.initial_average_weight_g, Decimal('9.75'))