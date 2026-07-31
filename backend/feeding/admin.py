from django.contrib import admin

from .models import FeedingRecommendation, FeedingSession


class FeedingSessionInline(admin.TabularInline):
    model = FeedingSession
    extra = 0


@admin.register(FeedingRecommendation)
class FeedingRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        'pond',
        'recommendation_date',
        'recommended_feed_kg',
        'feed_type',
        'estimated_cost',
        'status',
    )
    list_filter = ('status', 'feed_type', 'recommendation_date')
    search_fields = ('pond__name', 'feed_type')
    inlines = (FeedingSessionInline,)


@admin.register(FeedingSession)
class FeedingSessionAdmin(admin.ModelAdmin):
    list_display = (
        'pond',
        'scheduled_at',
        'meal_number',
        'planned_feed_kg',
        'actual_feed_kg',
        'status',
    )
    list_filter = ('status', 'scheduled_at')
    search_fields = ('pond__name', 'recommendation__feed_type')
