from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DiseaseProfileViewSet,
    HealthAlertsView,
    HealthDashboardView,
    HealthRecommendationView,
    HealthRecordViewSet,
    TreatmentPlanViewSet,
)


router = DefaultRouter()
router.register('diseases', DiseaseProfileViewSet, basename='fish-health-disease')
router.register('health-records', HealthRecordViewSet, basename='fish-health-record')
router.register('treatments', TreatmentPlanViewSet, basename='fish-health-treatment')

urlpatterns = [
    path('dashboard/', HealthDashboardView.as_view(), name='fish-health-dashboard'),
    path('recommendation/', HealthRecommendationView.as_view(), name='fish-health-recommendation'),
    path('alerts/', HealthAlertsView.as_view(), name='fish-health-alerts'),
    path('', include(router.urls)),
]
