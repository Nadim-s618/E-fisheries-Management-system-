from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from market_analysis.models import MarketPriceSnapshot
from market_analysis.serializers import MarketPriceSnapshotSerializer


class MarketPriceSnapshotSerializerUnitTests(SimpleTestCase):
    def build_snapshot(self):
        return MarketPriceSnapshot(
            id=7, fish_name='Rui', division='Dhaka', recorded_date=date(2026, 8, 12),
            price_per_kg=Decimal('350.00'),
            demand_level=MarketPriceSnapshot.DemandLevel.HIGH, source='Generated sample',
        )

    def test_serializes_supported_snapshot_fields(self):
        data = MarketPriceSnapshotSerializer(self.build_snapshot()).data
        self.assertEqual(data['fish_name'], 'Rui')
        self.assertEqual(data['division'], 'Dhaka')
        self.assertEqual(data['recorded_date'], '2026-08-12')
        self.assertEqual(data['price_per_kg'], '350.00')
        self.assertEqual(data['demand_level'], 'High')

    def test_all_snapshot_fields_are_read_only(self):
        serializer = MarketPriceSnapshotSerializer(data={
            'fish_name': 'Katla',
            'division': 'Sylhet',
            'price_per_kg': '400.00',
        })
        self.assertEqual(set(serializer.Meta.read_only_fields), set(serializer.fields))
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, {})
