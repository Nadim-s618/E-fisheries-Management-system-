from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from stocks.models import FishStock

from .models import MarketListing, MarketOrder
from .serializers import MarketListingSerializer, MarketOrderSerializer, MarketProfileSerializer
from .services import get_or_create_market_profile, recommend_price


class MarketProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        profile = get_or_create_market_profile(request.user)
        return Response(MarketProfileSerializer(profile).data)

    def patch(self, request):
        profile = get_or_create_market_profile(request.user)
        serializer = MarketProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PriceRecommendationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return self.recommend(request, request.query_params)

    def post(self, request):
        return self.recommend(request, request.data)

    def recommend(self, request, data):
        species = data.get('species', '')
        location = data.get('location', '')
        quantity_kg = data.get('quantity_kg') or data.get('quantity') or 0
        fish_stock_id = data.get('fish_stock')

        if fish_stock_id:
            stock = FishStock.objects.select_related('pond', 'pond__owner').filter(pk=fish_stock_id).first()
            if not stock or (not request.user.is_staff and stock.pond.owner_id != request.user.id):
                raise ValidationError({'fish_stock': 'Fish stock not found.'})
            species = species or stock.species
            location = location or stock.pond.location

        return Response(recommend_price(species, location, quantity_kg))


class MarketListingViewSet(viewsets.ModelViewSet):
    serializer_class = MarketListingSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        queryset = (
            MarketListing.objects
            .select_related('seller', 'fish_stock')
            .annotate(order_count=Count('orders'))
        )

        if self.request.query_params.get('mine') in {'1', 'true', 'yes'}:
            return queryset.filter(seller=self.request.user)
        if self.request.user.is_staff:
            return queryset

        return queryset.filter(status=MarketListing.Status.ACTIVE)

    def perform_update(self, serializer):
        listing = self.get_object()
        if not self.request.user.is_staff and listing.seller_id != self.request.user.id:
            raise PermissionDenied('Only the seller can update this listing.')
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.seller_id != self.request.user.id:
            raise PermissionDenied('Only the seller can delete this listing.')
        instance.delete()


class MarketOrderViewSet(viewsets.ModelViewSet):
    serializer_class = MarketOrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = MarketOrder.objects.select_related('listing', 'listing__seller', 'buyer')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(Q(buyer=self.request.user) | Q(listing__seller=self.request.user))

    def perform_update(self, serializer):
        order = self.get_object()
        if not self.request.user.is_staff and order.buyer_id != self.request.user.id:
            raise PermissionDenied('Only the buyer can edit this order.')
        if order.status != MarketOrder.Status.PENDING:
            raise ValidationError({'status': 'Only pending orders can be edited.'})
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.buyer_id != self.request.user.id:
            raise PermissionDenied('Only the buyer can delete this order.')
        if instance.status != MarketOrder.Status.PENDING:
            raise ValidationError({'status': 'Only pending orders can be deleted.'})
        instance.delete()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        return self._seller_transition(
            pk,
            MarketOrder.Status.ACCEPTED,
            seller_note=request.data.get('seller_note', ''),
            reserve_stock=True,
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._seller_transition(
            pk,
            MarketOrder.Status.REJECTED,
            seller_note=request.data.get('seller_note', ''),
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        return self._seller_transition(
            pk,
            MarketOrder.Status.COMPLETED,
            seller_note=request.data.get('seller_note', ''),
            allowed_current={MarketOrder.Status.ACCEPTED},
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if not request.user.is_staff and order.buyer_id != request.user.id:
            raise PermissionDenied('Only the buyer can cancel this order.')
        if order.status != MarketOrder.Status.PENDING:
            raise ValidationError({'status': 'Only pending orders can be cancelled.'})
        order.status = MarketOrder.Status.CANCELLED
        order.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(order).data)

    @transaction.atomic
    def _seller_transition(
        self,
        pk,
        next_status,
        seller_note='',
        reserve_stock=False,
        allowed_current=None,
    ):
        queryset = (
            MarketOrder.objects
            .select_for_update()
            .select_related('listing', 'listing__seller', 'buyer')
        )
        order = get_object_or_404(queryset, pk=pk)
        if not self.request.user.is_staff and order.listing.seller_id != self.request.user.id:
            raise PermissionDenied('Only the seller can update this order status.')
        allowed = allowed_current or {MarketOrder.Status.PENDING}
        if order.status not in allowed:
            raise ValidationError({'status': f'Order must be {", ".join(sorted(allowed))}.'})

        if reserve_stock:
            listing = MarketListing.objects.select_for_update().get(pk=order.listing_id)
            if listing.available_quantity_kg < order.quantity_kg:
                raise ValidationError({'quantity_kg': 'Requested quantity is no longer available.'})
            listing.available_quantity_kg -= order.quantity_kg
            if listing.available_quantity_kg <= Decimal('0'):
                listing.status = MarketListing.Status.SOLD_OUT
            listing.save(update_fields=['available_quantity_kg', 'status', 'updated_at'])

        order.status = next_status
        order.seller_note = seller_note
        order.save(update_fields=['status', 'seller_note', 'updated_at'])
        return Response(self.get_serializer(order).data, status=status.HTTP_200_OK)
