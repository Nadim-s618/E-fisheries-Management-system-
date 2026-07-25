from django.urls import path

from .views import WeatherDashboardView


urlpatterns = [
    path('dashboard/', WeatherDashboardView.as_view(), name='weather-dashboard'),
]
