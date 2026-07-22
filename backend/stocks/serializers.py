from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from growth.serializers import GrowthRecordSerializer
from ponds.serializers import PondSerializer

from .models import FishStock


class FishStockSerializer(serializers.ModelSerializer):
    pond = PondSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    growth_records = GrowthRecordSerializer(many=True, read_only=True)
    growth_analysis = serializers.SerializerMethodField()

    class Meta:
        model = FishStock
        fields = (
            'id',
            'pond',
            'species',
            'batch_name',
            'stocking_date',
            'initial_quantity',
            'current_quantity',
            'initial_average_weight_g',
            'status',
            'status_display',
            'notes',
            'growth_records',
            'growth_analysis',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'pond', 'created_at', 'updated_at')

    def get_growth_analysis(self, stock):
        latest_record = stock.growth_records.order_by('-recorded_date', '-id').first()
        latest_weight = (
            latest_record.average_weight_g
            if latest_record
            else stock.initial_average_weight_g
        )
        analysis_date = latest_record.recorded_date if latest_record else timezone.localdate()
        days_since_stocking = max((analysis_date - stock.stocking_date).days, 0)
        weight_gain = latest_weight - stock.initial_average_weight_g
        estimated_biomass_kg = (stock.current_quantity * latest_weight) / 1000
        total_feed = stock.growth_records.aggregate(total=Sum('feed_used_kg'))['total']
        biomass_gain_kg = (stock.current_quantity * weight_gain) / 1000
        fcr = None

        if total_feed and biomass_gain_kg > 0:
            fcr = total_feed / biomass_gain_kg

        daily_growth_rate = None
        if days_since_stocking > 0:
            daily_growth_rate = weight_gain / days_since_stocking

        survival_rate = None
        if stock.initial_quantity > 0:
            survival_rate = (stock.current_quantity / stock.initial_quantity) * 100

        return {
            'days_since_stocking': days_since_stocking,
            'latest_recorded_date': latest_record.recorded_date if latest_record else None,
            'latest_average_weight_g': round(float(latest_weight), 2),
            'weight_gain_g': round(float(weight_gain), 2),
            'daily_growth_rate_g': (
                round(float(daily_growth_rate), 2)
                if daily_growth_rate is not None
                else None
            ),
            'estimated_biomass_kg': round(float(estimated_biomass_kg), 2),
            'survival_rate_percent': (
                round(float(survival_rate), 2)
                if survival_rate is not None
                else None
            ),
            'total_feed_used_kg': round(float(total_feed), 2) if total_feed else None,
            'feed_conversion_ratio': round(float(fcr), 2) if fcr is not None else None,
            'growth_records_count': stock.growth_records.count(),
        }

    def validate_species(self, value):
        species = value.strip()
        if not species:
            raise serializers.ValidationError('Fish species is required.')
        return species

    def validate_batch_name(self, value):
        batch_name = value.strip()
        if not batch_name:
            raise serializers.ValidationError('Batch name is required.')
        return batch_name

    def validate_initial_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Initial quantity must be greater than zero.')
        return value

    def validate_current_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError('Current quantity cannot be negative.')
        return value

    def validate_initial_average_weight_g(self, value):
        if value <= 0:
            raise serializers.ValidationError('Initial average weight must be greater than zero.')
        return value

    def validate(self, attrs):
        pond = getattr(self.instance, 'pond', None) or self.context.get('pond')
        batch_name = attrs.get('batch_name', getattr(self.instance, 'batch_name', None))

        if pond and batch_name:
            duplicate_stocks = FishStock.objects.filter(
                pond=pond,
                batch_name__iexact=batch_name,
            )
            if self.instance:
                duplicate_stocks = duplicate_stocks.exclude(pk=self.instance.pk)
            if duplicate_stocks.exists():
                raise serializers.ValidationError({
                    'batch_name': 'This pond already has a stock batch with this name.',
                })

        return attrs
