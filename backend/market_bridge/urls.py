from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MarketListingViewSet,
    MarketOrderViewSet,
    MarketProfileView,
    PriceRecommendationView,
)


router = DefaultRouter()
router.register('listings', MarketListingViewSet, basename='market-listing')
router.register('orders', MarketOrderViewSet, basename='market-order')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', MarketProfileView.as_view(), name='market-profile'),
    path('price-recommendation/', PriceRecommendationView.as_view(), name='market-price-recommendation'),
]
