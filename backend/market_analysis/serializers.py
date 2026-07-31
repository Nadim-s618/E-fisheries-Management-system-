from rest_framework import serializers

from .models import MarketPriceSnapshot


class MarketPriceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPriceSnapshot
        fields = (
            'id',
            'fish_name',
            'division',
            'recorded_date',
            'price_per_kg',
            'demand_level',
            'source',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
