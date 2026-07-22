from django.contrib import admin

from .models import GrowthRecord


@admin.register(GrowthRecord)
class GrowthRecordAdmin(admin.ModelAdmin):
    list_display = (
        'stock',
        'recorded_date',
        'sample_count',
        'average_weight_g',
        'average_length_cm',
        'mortality_count',
        'feed_used_kg',
    )
    list_filter = ('recorded_date', 'stock__species')
    search_fields = ('stock__batch_name', 'stock__species', 'stock__pond__name')
    readonly_fields = ('created_at', 'updated_at')
