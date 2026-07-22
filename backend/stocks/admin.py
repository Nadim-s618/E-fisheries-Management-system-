from django.contrib import admin

from .models import FishStock


@admin.register(FishStock)
class FishStockAdmin(admin.ModelAdmin):
    list_display = (
        'batch_name',
        'species',
        'pond',
        'stocking_date',
        'initial_quantity',
        'current_quantity',
        'status',
    )
    list_filter = ('status', 'species', 'stocking_date')
    search_fields = ('batch_name', 'species', 'pond__name', 'pond__owner__email')
    readonly_fields = ('created_at', 'updated_at')
