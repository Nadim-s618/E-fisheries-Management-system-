from django.urls import path

from . import views


urlpatterns = [
    path('stocks/<int:stock_pk>/growth/', views.growth_list, name='growth-list'),
    path('growth/<int:pk>/', views.growth_detail, name='growth-detail'),
]
