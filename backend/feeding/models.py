from django.core.exceptions import ValidationError
from django.db import models

from ponds.models import Pond


class FeedingRecommendation(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACCEPTED = 'accepted', 'Accepted'
        EDITED = 'edited', 'Edited'
        COMPLETED = 'completed', 'Completed'
        SUPERSEDED = 'superseded', 'Superseded'

    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='feeding_recommendations',
    )
    recommendation_date = models.DateField()
    recommended_feed_kg = models.DecimalField(max_digits=9, decimal_places=2)
    feed_type = models.CharField(max_length=120, default='Floating Feed 32%')
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2, default=135.00)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2)
    meals = models.PositiveSmallIntegerField(default=2)
    schedule = models.JSONField(default=list)
    reasons = models.JSONField(default=list)
    input_summary = models.JSONField(default=dict)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-recommendation_date', '-created_at']
        indexes = [
            models.Index(fields=['pond', 'recommendation_date', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(recommended_feed_kg__gt=0),
                name='feeding_recommendation_feed_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_kg__gte=0),
                name='feeding_recommendation_price_not_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_cost__gte=0),
                name='feeding_recommendation_cost_not_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(meals__gt=0),
                name='feeding_recommendation_meals_positive',
            ),
        ]

    def clean(self):
        errors = {}

        if self.recommended_feed_kg is not None and self.recommended_feed_kg <= 0:
            errors['recommended_feed_kg'] = 'Recommended feed must be greater than zero.'

        if self.price_per_kg is not None and self.price_per_kg < 0:
            errors['price_per_kg'] = 'Feed price cannot be negative.'

        if self.meals is not None and self.meals <= 0:
            errors['meals'] = 'Meals must be greater than zero.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.pond} feeding on {self.recommendation_date}'


class FeedingSession(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        SKIPPED = 'skipped', 'Skipped'

    recommendation = models.ForeignKey(
        FeedingRecommendation,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='feeding_sessions',
    )
    meal_number = models.PositiveSmallIntegerField()
    scheduled_at = models.DateTimeField()
    planned_feed_kg = models.DecimalField(max_digits=9, decimal_places=2)
    actual_feed_kg = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at', 'meal_number']
        constraints = [
            models.UniqueConstraint(
                fields=['recommendation', 'meal_number'],
                name='unique_feeding_session_meal_per_recommendation',
            ),
            models.CheckConstraint(
                condition=models.Q(meal_number__gt=0),
                name='feeding_session_meal_number_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(planned_feed_kg__gt=0),
                name='feeding_session_planned_feed_positive',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(actual_feed_kg__isnull=True)
                    | models.Q(actual_feed_kg__gt=0)
                ),
                name='feeding_session_actual_feed_positive_when_set',
            ),
        ]

    def __str__(self):
        return f'{self.pond} meal {self.meal_number} at {self.scheduled_at:%Y-%m-%d %H:%M}'
