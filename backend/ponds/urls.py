from django.urls import path

from . import views


urlpatterns = [
    path('ponds/', views.pond_list, name='pond-list'),
    path('ponds/<int:pk>/', views.pond_detail, name='pond-detail'),
]
