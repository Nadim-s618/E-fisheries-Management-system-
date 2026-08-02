from django.contrib import admin

from .models import DiseaseProfile, HealthRecord, TreatmentPlan


@admin.register(DiseaseProfile)
class DiseaseProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_level', 'is_active', 'updated_at')
    list_filter = ('risk_level', 'is_active')
    search_fields = ('name', 'description')


@admin.register(HealthRecord)
class HealthRecordAdmin(admin.ModelAdmin):
    list_display = ('pond', 'species', 'severity', 'status', 'mortality_count', 'observed_at')
    list_filter = ('severity', 'status', 'observed_at')
    search_fields = ('pond__name', 'species', 'symptom_notes')


@admin.register(TreatmentPlan)
class TreatmentPlanAdmin(admin.ModelAdmin):
    list_display = ('medicine_name', 'pond', 'status', 'start_date', 'end_date', 'cost')
    list_filter = ('status', 'start_date')
    search_fields = ('medicine_name', 'pond__name', 'dosage')
