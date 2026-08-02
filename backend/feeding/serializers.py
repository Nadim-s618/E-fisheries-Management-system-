from decimal import Decimal

from rest_framework import serializers

from .models import FeedingRecommendation, FeedingSession


class FeedingSessionSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)

    class Meta:
        model = FeedingSession
        fields = (
            'id',
            'recommendation',
            'pond',
            'pond_name',
            'meal_number',
            'scheduled_at',
            'planned_feed_kg',
            'actual_feed_kg',
            'status',
            'completed_at',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'recommendation',
            'pond',
            'pond_name',
            'meal_number',
            'scheduled_at',
            'planned_feed_kg',
            'status',
            'completed_at',
            'created_at',
            'updated_at',
        )


class FeedingRecommendationSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)
    sessions = FeedingSessionSerializer(many=True, read_only=True)
    computed_status = serializers.SerializerMethodField()

    class Meta:
        model = FeedingRecommendation
        fields = (
            'id',
            'pond',
            'pond_name',
            'recommendation_date',
            'recommended_feed_kg',
            'feed_type',
            'price_per_kg',
            'estimated_cost',
            'meals',
            'schedule',
            'reasons',
            'input_summary',
            'status',
            'computed_status',
            'sessions',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_computed_status(self, recommendation):
        sessions = list(recommendation.sessions.all())

        if recommendation.status == FeedingRecommendation.Status.DRAFT:
            return 'Draft'
        if sessions and all(session.status == FeedingSession.Status.COMPLETED for session in sessions):
            return 'Completed'
        if any(session.status == FeedingSession.Status.COMPLETED for session in sessions):
            return 'In Progress'
        return recommendation.get_status_display()


class FeedingRecommendationEditSerializer(serializers.Serializer):
    recommended_feed_kg = serializers.DecimalField(max_digits=9, decimal_places=2, min_value=Decimal('0.01'))
    feed_type = serializers.CharField(max_length=120)
    price_per_kg = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.00'))
    meals = serializers.IntegerField(min_value=1, max_value=4)
    meal_times = serializers.ListField(
        child=serializers.RegexField(regex=r'^\d{2}:\d{2}$'),
        min_length=1,
        max_length=4,
        required=False,
    )

    def validate(self, attrs):
        meal_times = attrs.get('meal_times')
        meals = attrs.get('meals')

        if meal_times and len(meal_times) != meals:
            raise serializers.ValidationError({
                'meal_times': 'Meal times must match the number of meals.',
            })

        return attrs


class FeedingSessionCompleteSerializer(serializers.Serializer):
    actual_feed_kg = serializers.DecimalField(
        max_digits=9,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=False,
    )
    notes = serializers.CharField(required=False, allow_blank=True)
