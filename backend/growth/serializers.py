from rest_framework import serializers

from .models import GrowthRecord


class GrowthRecordSerializer(serializers.ModelSerializer):
    stock = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = GrowthRecord
        fields = (
            'id',
            'stock',
            'recorded_date',
            'sample_count',
            'average_weight_g',
            'average_length_cm',
            'mortality_count',
            'feed_used_kg',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'stock', 'created_at', 'updated_at')

    def validate_sample_count(self, value):
        if value <= 0:
            raise serializers.ValidationError('Sample count must be greater than zero.')
        return value

    def validate_average_weight_g(self, value):
        if value <= 0:
            raise serializers.ValidationError('Average weight must be greater than zero.')
        return value

    def validate_average_length_cm(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Average length must be greater than zero.')
        return value

    def validate_mortality_count(self, value):
        if value < 0:
            raise serializers.ValidationError('Mortality count cannot be negative.')
        return value

    def validate_feed_used_kg(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Feed used must be greater than zero.')
        return value

    def validate(self, attrs):
        stock = getattr(self.instance, 'stock', None) or self.context.get('stock')
        recorded_date = attrs.get('recorded_date', getattr(self.instance, 'recorded_date', None))

        if stock and recorded_date and recorded_date < stock.stocking_date:
            raise serializers.ValidationError({
                'recorded_date': 'Growth date cannot be before the stocking date.',
            })

        if stock and recorded_date:
            duplicate_records = GrowthRecord.objects.filter(
                stock=stock,
                recorded_date=recorded_date,
            )
            if self.instance:
                duplicate_records = duplicate_records.exclude(pk=self.instance.pk)
            if duplicate_records.exists():
                raise serializers.ValidationError({
                    'recorded_date': 'This stock already has a growth record for this date.',
                })

        return attrs
