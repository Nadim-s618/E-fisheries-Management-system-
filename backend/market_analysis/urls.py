from django.urls import path

from .views import MarketAnalysisDashboardView


urlpatterns = [
    path('dashboard/', MarketAnalysisDashboardView.as_view(), name='market-analysis-dashboard'),
]
