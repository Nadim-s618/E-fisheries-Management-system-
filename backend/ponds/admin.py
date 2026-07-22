from django.contrib import admin

from .models import Pond


@admin.register(Pond)
class PondAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'owner',
        'location',
        'area_decimal',
        'average_depth_ft',
        'stocking_capacity',
        'status',
    )
    list_filter = ('status', 'water_source', 'created_at')
    search_fields = ('name', 'location', 'owner__username', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
