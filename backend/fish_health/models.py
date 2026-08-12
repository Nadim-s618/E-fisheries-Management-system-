from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ponds.models import Pond
from stocks.models import FishStock


class DiseaseProfile(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = 'Low', 'Low'
        MODERATE = 'Moderate', 'Moderate'
        HIGH = 'High', 'High'
        CRITICAL = 'Critical', 'Critical'

    name = models.CharField(max_length=160, unique=True)
    species = models.JSONField(default=list, blank=True)
    symptoms = models.JSONField(default=list)
    description = models.TextField()
    risk_level = models.CharField(
        max_length=16,
        choices=RiskLevel.choices,
        default=RiskLevel.MODERATE,
    )
    recommended_treatments = models.JSONField(default=list, blank=True)
    treatment_protocols = models.JSONField(default=list, blank=True)
    maintenance_actions = models.JSONField(default=list, blank=True)
    prevention = models.JSONField(default=list, blank=True)
    environmental_triggers = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if not (self.name or '').strip():
            raise ValidationError({'name': 'Disease name is required.'})
        if not self.symptoms:
            raise ValidationError({'symptoms': 'At least one symptom is required.'})

    def __str__(self):
        return self.name


class HealthRecord(models.Model):
    class Severity(models.TextChoices):
        LOW = 'Low', 'Low'
        MODERATE = 'Moderate', 'Moderate'
        HIGH = 'High', 'High'
        CRITICAL = 'Critical', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'Open', 'Open'
        MONITORING = 'Monitoring', 'Monitoring'
        TREATMENT = 'Treatment', 'Treatment'
        RESOLVED = 'Resolved', 'Resolved'

    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='health_records',
    )
    fish_stock = models.ForeignKey(
        FishStock,
        on_delete=models.SET_NULL,
        related_name='health_records',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fish_health_records',
    )
    observed_at = models.DateTimeField()
    species = models.CharField(max_length=120, blank=True)
    symptoms = models.JSONField(default=list, blank=True)
    symptom_notes = models.TextField(blank=True)
    abnormal_behavior = models.TextField(blank=True)
    affected_count = models.PositiveIntegerField(default=0)
    mortality_count = models.PositiveIntegerField(default=0)
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.MODERATE,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    water_quality_snapshot = models.JSONField(default=dict, blank=True)
    weather_snapshot = models.JSONField(default=dict, blank=True)
    possible_diseases = models.JSONField(default=list, blank=True)
    ai_recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-observed_at', '-created_at']
        indexes = [
            models.Index(fields=['pond', '-observed_at']),
            models.Index(fields=['status', 'severity']),
        ]

    def clean(self):
        if self.fish_stock and self.fish_stock.pond_id != self.pond_id:
            raise ValidationError({'fish_stock': 'Fish stock must belong to the selected pond.'})
        if self.affected_count < 0:
            raise ValidationError({'affected_count': 'Affected count cannot be negative.'})
        if self.mortality_count < 0:
            raise ValidationError({'mortality_count': 'Mortality count cannot be negative.'})

    def __str__(self):
        return f'{self.pond} health record on {self.observed_at:%Y-%m-%d}'


class TreatmentPlan(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'Planned', 'Planned'
        ACTIVE = 'Active', 'Active'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    pond = models.ForeignKey(
        Pond,
        on_delete=models.CASCADE,
        related_name='treatment_plans',
    )
    fish_stock = models.ForeignKey(
        FishStock,
        on_delete=models.SET_NULL,
        related_name='treatment_plans',
        null=True,
        blank=True,
    )
    health_record = models.ForeignKey(
        HealthRecord,
        on_delete=models.SET_NULL,
        related_name='treatment_plans',
        null=True,
        blank=True,
    )
    disease = models.ForeignKey(
        DiseaseProfile,
        on_delete=models.SET_NULL,
        related_name='treatment_plans',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fish_treatment_plans',
    )
    medicine_name = models.CharField(max_length=160)
    dosage = models.CharField(max_length=160)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    instructions = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    outcome_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']
        indexes = [
            models.Index(fields=['pond', 'status']),
        ]

    def clean(self):
        if self.fish_stock and self.fish_stock.pond_id != self.pond_id:
            raise ValidationError({'fish_stock': 'Fish stock must belong to the selected pond.'})
        if self.health_record and self.health_record.pond_id != self.pond_id:
            raise ValidationError({'health_record': 'Health record must belong to the selected pond.'})
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'End date cannot be before start date.'})
        if self.cost < 0:
            raise ValidationError({'cost': 'Cost cannot be negative.'})

    def __str__(self):
        return f'{self.medicine_name} for {self.pond}'


class TreatmentTrackingEntry(models.Model):
    treatment = models.ForeignKey(
        TreatmentPlan,
        on_delete=models.CASCADE,
        related_name='tracking_entries',
    )
    status = models.CharField(max_length=16, choices=TreatmentPlan.Status.choices)
    administered_dosage = models.CharField(max_length=160, blank=True)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='treatment_tracking_entries',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['treatment', '-created_at']),
        ]
