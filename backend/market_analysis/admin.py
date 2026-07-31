from django.contrib import admin

from .models import MarketPriceSnapshot


@admin.register(MarketPriceSnapshot)
class MarketPriceSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        'fish_name',
        'division',
        'recorded_date',
        'price_per_kg',
        'demand_level',
        'source',
    )
    list_filter = ('division', 'fish_name', 'demand_level', 'recorded_date')
    search_fields = ('fish_name', 'division')
    readonly_fields = ('created_at', 'updated_at')
