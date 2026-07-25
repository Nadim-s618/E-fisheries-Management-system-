import math

from rest_framework import serializers

from ponds.models import Pond

from .models import WaterQualityReading


class WaterQualityReadingSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)

    class Meta:
        model = WaterQualityReading
        fields = (
            'id',
            'pond',
            'pond_name',
            'temperature',
            'ph',
            'dissolved_oxygen',
            'ammonia',
            'nitrite',
            'nitrate',
            'turbidity',
            'salinity',
            'water_level',
            'overall_status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'pond_name', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user and request.user.is_authenticated:
            if request.user.is_staff:
                self.fields['pond'].queryset = Pond.objects.all()
            else:
                self.fields['pond'].queryset = Pond.objects.filter(owner=request.user)

    def validate_temperature(self, value):
        return self._validate_range(value, 'temperature', minimum=0, maximum=50)

    def validate_ph(self, value):
        return self._validate_range(value, 'pH', minimum=0, maximum=14)

    def validate_dissolved_oxygen(self, value):
        return self._validate_range(value, 'dissolved oxygen', minimum=0, maximum=30)

    def validate_ammonia(self, value):
        return self._validate_range(value, 'ammonia', minimum=0, maximum=100)

    def validate_nitrite(self, value):
        return self._validate_range(value, 'nitrite', minimum=0, maximum=100)

    def validate_nitrate(self, value):
        return self._validate_range(value, 'nitrate', minimum=0, maximum=500)

    def validate_turbidity(self, value):
        return self._validate_range(value, 'turbidity', minimum=0, maximum=1000)

    def validate_salinity(self, value):
        if value is None:
            return value
        return self._validate_range(value, 'salinity', minimum=0, maximum=80)

    def validate_water_level(self, value):
        return self._validate_range(value, 'water level', minimum=0, maximum=100)

    def _validate_range(self, value, field_name, minimum, maximum):
        if not math.isfinite(value):
            raise serializers.ValidationError(f'{field_name.title()} must be a finite number.')

        if value < minimum:
            raise serializers.ValidationError(f'{field_name.title()} cannot be less than {minimum}.')

        if value > maximum:
            raise serializers.ValidationError(f'{field_name.title()} cannot be greater than {maximum}.')

        return value
