from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    WaterQualityCompareView,
    WaterQualityDashboardView,
    WaterQualityGraphView,
    WaterQualityHistoryView,
    WaterQualityReadingViewSet,
)


router = DefaultRouter()
router.register(
    'water-quality-readings',
    WaterQualityReadingViewSet,
    basename='water-quality-reading',
)

urlpatterns = [
    path('dashboard/', WaterQualityDashboardView.as_view(), name='water-quality-dashboard'),
    path('history/', WaterQualityHistoryView.as_view(), name='water-quality-history'),
    path('graph/', WaterQualityGraphView.as_view(), name='water-quality-graph'),
    path('compare/', WaterQualityCompareView.as_view(), name='water-quality-compare'),
    path('', include(router.urls)),
]
