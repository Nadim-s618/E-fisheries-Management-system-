from django.contrib import admin

from .models import MarketListing, MarketOrder, MarketProfile


@admin.register(MarketProfile)
class MarketProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_approved', 'business_name', 'phone', 'updated_at')
    list_filter = ('role', 'is_approved')
    search_fields = ('user__username', 'user__email', 'business_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MarketListing)
class MarketListingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'seller',
        'species',
        'source_type',
        'available_quantity_kg',
        'unit_price',
        'status',
        'created_at',
    )
    list_filter = ('status', 'source_type', 'species', 'created_at')
    search_fields = ('title', 'species', 'seller__username', 'seller__email', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MarketOrder)
class MarketOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'listing',
        'buyer',
        'quantity_kg',
        'total_price',
        'status',
        'created_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('listing__title', 'buyer__username', 'buyer__email')
    readonly_fields = ('created_at', 'updated_at')
