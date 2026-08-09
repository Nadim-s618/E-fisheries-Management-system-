from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ponds.models import Pond


def make_pond(**overrides):
    defaults = {
        'owner_id': 1,
        'name': 'North Pond',
        'location': 'Natore',
        'area_decimal': Decimal('24.00'),
        'average_depth_ft': Decimal('5.00'),
        'stocking_capacity': 2000,
    }
    defaults.update(overrides)
    return Pond(**defaults)


class PondModelUnitTests(SimpleTestCase):
    def test_clean_accepts_positive_measurements(self):
        pond = make_pond()

        pond.clean()

        self.assertEqual(pond.name, 'North Pond')

    def test_string_returns_pond_name(self):
        self.assertEqual(str(make_pond(name='Madhnagar Pond')), 'Madhnagar Pond')

    def test_default_water_source_is_mixed(self):
        self.assertEqual(make_pond().water_source, Pond.WaterSource.MIXED)

    def test_default_status_is_active(self):
        self.assertEqual(make_pond().status, Pond.Status.ACTIVE)

    def test_notes_default_to_empty_string(self):
        self.assertEqual(make_pond().notes, '')

    def test_water_source_choices(self):
        self.assertEqual(Pond.WaterSource.RAINWATER, 'rainwater')
        self.assertEqual(Pond.WaterSource.DEEP_TUBEWELL, 'deep_tubewell')
        self.assertEqual(Pond.WaterSource.MIXED.label, 'Mixed')

    def test_status_choices(self):
        self.assertEqual(Pond.Status.ACTIVE.label, 'Active')
        self.assertEqual(Pond.Status.MAINTENANCE.label, 'Maintenance')
        self.assertEqual(Pond.Status.INACTIVE.label, 'Inactive')

    def test_clean_rejects_non_positive_measurements(self):
        pond = make_pond(
            area_decimal=Decimal('0.00'),
            average_depth_ft=Decimal('-1.00'),
            stocking_capacity=0,
        )

        with self.assertRaises(ValidationError) as context:
            pond.clean()

        self.assertEqual(
            set(context.exception.message_dict),
            {'area_decimal', 'average_depth_ft', 'stocking_capacity'},
        )

    def test_meta_configuration(self):
        self.assertEqual(Pond._meta.ordering, ['name'])
        self.assertEqual(Pond._meta.get_field('name').max_length, 120)
        self.assertEqual(Pond._meta.get_field('location').max_length, 180)
        self.assertEqual(Pond._meta.get_field('area_decimal').decimal_places, 2)
        self.assertEqual(Pond._meta.get_field('average_depth_ft').decimal_places, 2)
        self.assertTrue(Pond._meta.get_field('notes').blank)

    def test_constraint_names_are_present(self):
        constraint_names = {constraint.name for constraint in Pond._meta.constraints}
        self.assertEqual(constraint_names, {
            'unique_pond_name_per_owner',
            'pond_area_decimal_positive',
            'pond_average_depth_positive',
            'pond_stocking_capacity_positive',
        })
