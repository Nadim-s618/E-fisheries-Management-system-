from django.utils import timezone
from rest_framework import serializers

from core.serializers import NotificationSerializer
from ponds.models import Pond
from stocks.models import FishStock

from .models import DiseaseProfile, HealthRecord, TreatmentPlan
from .services.core.diagnosis import diagnose_health_record
from .services.water_quality.context import get_latest_water_quality_snapshot
from .services.weather.context import get_latest_weather_snapshot


class DiseaseProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseProfile
        fields = (
            'id',
            'name',
            'species',
            'symptoms',
            'description',
            'risk_level',
            'recommended_treatments',
            'treatment_protocols',
            'maintenance_actions',
            'prevention',
            'environmental_triggers',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class HealthRecordSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)
    fish_stock_name = serializers.CharField(source='fish_stock.batch_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = HealthRecord
        fields = (
            'id',
            'pond',
            'pond_name',
            'fish_stock',
            'fish_stock_name',
            'created_by_name',
            'observed_at',
            'species',
            'symptoms',
            'symptom_notes',
            'abnormal_behavior',
            'affected_count',
            'mortality_count',
            'severity',
            'status',
            'water_quality_snapshot',
            'weather_snapshot',
            'possible_diseases',
            'ai_recommendation',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'pond_name',
            'fish_stock_name',
            'created_by_name',
            'severity',
            'water_quality_snapshot',
            'weather_snapshot',
            'possible_diseases',
            'ai_recommendation',
            'created_at',
            'updated_at',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user and request.user.is_authenticated:
            ponds = Pond.objects.all() if request.user.is_staff else Pond.objects.filter(owner=request.user)
            self.fields['pond'].queryset = ponds
            self.fields['fish_stock'].queryset = FishStock.objects.filter(pond__in=ponds)

    def validate_symptoms(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Symptoms must be a list.')
        return [str(item).strip() for item in value if str(item).strip()]

    def validate(self, attrs):
        pond = attrs.get('pond', getattr(self.instance, 'pond', None))
        fish_stock = attrs.get('fish_stock', getattr(self.instance, 'fish_stock', None))
        symptom_notes = attrs.get('symptom_notes', getattr(self.instance, 'symptom_notes', ''))
        symptoms = attrs.get('symptoms', getattr(self.instance, 'symptoms', []))

        if fish_stock and pond and fish_stock.pond_id != pond.id:
            raise serializers.ValidationError({'fish_stock': 'Fish stock must belong to the selected pond.'})
        if not symptoms and not (symptom_notes or '').strip():
            raise serializers.ValidationError('Select symptoms or describe symptoms in notes.')

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        pond = validated_data['pond']

        validated_data.setdefault('observed_at', timezone.now())
        validated_data['created_by'] = request.user
        validated_data['water_quality_snapshot'] = get_latest_water_quality_snapshot(pond)
        validated_data['weather_snapshot'] = get_latest_weather_snapshot(pond)

        if not validated_data.get('species') and validated_data.get('fish_stock'):
            validated_data['species'] = validated_data['fish_stock'].species

        record = HealthRecord.objects.create(**validated_data)
        return diagnose_health_record(record)

    def update(self, instance, validated_data):
        pond = validated_data.get('pond', instance.pond)
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.water_quality_snapshot = get_latest_water_quality_snapshot(pond)
        instance.weather_snapshot = get_latest_weather_snapshot(pond)
        if not instance.species and instance.fish_stock:
            instance.species = instance.fish_stock.species
        instance.save()
        return diagnose_health_record(instance)


class TreatmentPlanSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)
    fish_stock_name = serializers.CharField(source='fish_stock.batch_name', read_only=True)
    disease_name = serializers.CharField(source='disease.name', read_only=True)

    class Meta:
        model = TreatmentPlan
        fields = (
            'id',
            'pond',
            'pond_name',
            'fish_stock',
            'fish_stock_name',
            'health_record',
            'disease',
            'disease_name',
            'medicine_name',
            'dosage',
            'start_date',
            'end_date',
            'cost',
            'instructions',
            'status',
            'outcome_notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'pond_name', 'fish_stock_name', 'disease_name', 'created_at', 'updated_at')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')

        if request and request.user and request.user.is_authenticated:
            ponds = Pond.objects.all() if request.user.is_staff else Pond.objects.filter(owner=request.user)
            self.fields['pond'].queryset = ponds
            self.fields['fish_stock'].queryset = FishStock.objects.filter(pond__in=ponds)
            self.fields['health_record'].queryset = HealthRecord.objects.filter(pond__in=ponds)
            self.fields['disease'].queryset = DiseaseProfile.objects.filter(is_active=True)

    def validate(self, attrs):
        pond = attrs.get('pond', getattr(self.instance, 'pond', None))
        fish_stock = attrs.get('fish_stock', getattr(self.instance, 'fish_stock', None))
        health_record = attrs.get('health_record', getattr(self.instance, 'health_record', None))
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        if fish_stock and pond and fish_stock.pond_id != pond.id:
            raise serializers.ValidationError({'fish_stock': 'Fish stock must belong to the selected pond.'})
        if health_record and pond and health_record.pond_id != pond.id:
            raise serializers.ValidationError({'health_record': 'Health record must belong to the selected pond.'})
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'End date cannot be before start date.'})

        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class HealthAlertSerializer(NotificationSerializer):
    pass
