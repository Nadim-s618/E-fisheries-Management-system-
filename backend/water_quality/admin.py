from django.contrib import admin

from .models import WaterQualityReading


@admin.register(WaterQualityReading)
class WaterQualityReadingAdmin(admin.ModelAdmin):
    list_display = (
        'pond',
        'temperature',
        'ph',
        'dissolved_oxygen',
        'overall_status',
        'created_at',
    )
    list_filter = ('overall_status', 'created_at', 'updated_at')
    search_fields = ('pond__name',)
    readonly_fields = ('created_at', 'updated_at')
