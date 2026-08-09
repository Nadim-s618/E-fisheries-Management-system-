from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MarketListingViewSet,
    MarketOrderViewSet,
    MarketProfileView,
    PublicMashrafeeCartOrderView,
    PublicMashrafeeOrderView,
    PublicMashrafeeOrderTrackingView,
    PublicMashrafeeStoreView,
    PriceRecommendationView,
)


router = DefaultRouter()
router.register('listings', MarketListingViewSet, basename='market-listing')
router.register('orders', MarketOrderViewSet, basename='market-order')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', MarketProfileView.as_view(), name='market-profile'),
    path('price-recommendation/', PriceRecommendationView.as_view(), name='market-price-recommendation'),
    path('public-store/', PublicMashrafeeStoreView.as_view(), name='public-mashrafee-store'),
    path('public-store/orders/', PublicMashrafeeOrderView.as_view(), name='public-mashrafee-order'),
    path('public-store/cart-orders/', PublicMashrafeeCartOrderView.as_view(), name='public-mashrafee-cart-order'),
    path('public-store/track/<str:code>/', PublicMashrafeeOrderTrackingView.as_view(), name='public-mashrafee-order-track'),
]
