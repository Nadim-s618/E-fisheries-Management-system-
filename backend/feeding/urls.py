from django.urls import path

from . import views


urlpatterns = [
    path('dashboard/', views.feeding_dashboard, name='feeding-dashboard'),
    path('history/', views.feeding_history, name='feeding-history'),
    path('recommendations/<int:pk>/accept/', views.accept_recommendation, name='feeding-recommendation-accept'),
    path('recommendations/<int:pk>/edit/', views.edit_recommendation, name='feeding-recommendation-edit'),
    path('sessions/<int:pk>/complete/', views.complete_session, name='feeding-session-complete'),
]
