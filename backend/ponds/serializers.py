from rest_framework import serializers

from core.serializers import UserSerializer

from .models import Pond


class PondSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    water_source_display = serializers.CharField(
        source='get_water_source_display',
        read_only=True,
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Pond
        fields = (
            'id',
            'owner',
            'name',
            'location',
            'area_decimal',
            'average_depth_ft',
            'water_source',
            'water_source_display',
            'stocking_capacity',
            'status',
            'status_display',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError('Pond name is required.')
        return name

    def validate_location(self, value):
        location = value.strip()
        if not location:
            raise serializers.ValidationError('Pond location is required.')
        return location

    def validate_area_decimal(self, value):
        if value <= 0:
            raise serializers.ValidationError('Pond area must be greater than zero.')
        return value

    def validate_average_depth_ft(self, value):
        if value <= 0:
            raise serializers.ValidationError('Average depth must be greater than zero.')
        return value

    def validate_stocking_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Stocking capacity must be greater than zero.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        owner = getattr(self.instance, 'owner', None) or getattr(request, 'user', None)
        name = attrs.get('name', getattr(self.instance, 'name', None))

        if owner and name:
            duplicate_ponds = Pond.objects.filter(owner=owner, name__iexact=name)
            if self.instance:
                duplicate_ponds = duplicate_ponds.exclude(pk=self.instance.pk)
            if duplicate_ponds.exists():
                raise serializers.ValidationError({
                    'name': 'You already have a pond with this name.',
                })

        return attrs
