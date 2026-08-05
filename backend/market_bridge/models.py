from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from stocks.models import FishStock


class MarketProfile(models.Model):
    class Role(models.TextChoices):
        BUYER = 'buyer', 'Buyer'
        SELLER = 'seller', 'Seller'
        BOTH = 'both', 'Buyer and seller'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='market_profile',
    )
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.BOTH)
    is_approved = models.BooleanField(default=True)
    business_name = models.CharField(max_length=140, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=220, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    @property
    def can_buy(self):
        return self.is_approved and self.role in {self.Role.BUYER, self.Role.BOTH}

    @property
    def can_sell(self):
        return self.is_approved and self.role in {self.Role.SELLER, self.Role.BOTH}

    def __str__(self):
        return f'{self.user} market profile'


class MarketListing(models.Model):
    class SourceType(models.TextChoices):
        INVENTORY = 'inventory', 'From stock'
        MANUAL = 'manual', 'Manual stock'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'
        SOLD_OUT = 'sold_out', 'Sold out'
        CLOSED = 'closed', 'Closed'

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='market_listings',
    )
    fish_stock = models.ForeignKey(
        FishStock,
        on_delete=models.SET_NULL,
        related_name='market_listings',
        null=True,
        blank=True,
    )
    source_type = models.CharField(
        max_length=16,
        choices=SourceType.choices,
        default=SourceType.MANUAL,
    )
    species = models.CharField(max_length=120)
    title = models.CharField(max_length=160)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=180)
    available_from = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    photo = models.FileField(upload_to='market_bridge/listings/', null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at'], name='mb_listing_status_idx'),
            models.Index(fields=['seller', 'status'], name='mb_listing_seller_status_idx'),
            models.Index(fields=['species', 'location'], name='mb_listing_species_loc_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_kg__gt=0),
                name='market_listing_quantity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(available_quantity_kg__gte=0),
                name='market_listing_available_not_negative',
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gt=0),
                name='market_listing_unit_price_positive',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(suggested_price__isnull=True)
                    | models.Q(suggested_price__gt=0)
                ),
                name='market_listing_suggested_price_positive',
            ),
        ]

    @property
    def total_value(self):
        return self.available_quantity_kg * self.unit_price

    def clean(self):
        errors = {}

        if self.source_type == self.SourceType.INVENTORY and not self.fish_stock_id:
            errors['fish_stock'] = 'Inventory listings must reference a fish stock.'
        if self.quantity_kg is not None and self.quantity_kg <= Decimal('0'):
            errors['quantity_kg'] = 'Quantity must be greater than zero.'
        if self.available_quantity_kg is not None and self.available_quantity_kg < Decimal('0'):
            errors['available_quantity_kg'] = 'Available quantity cannot be negative.'
        if (
            self.quantity_kg is not None
            and self.available_quantity_kg is not None
            and self.available_quantity_kg > self.quantity_kg
        ):
            errors['available_quantity_kg'] = 'Available quantity cannot exceed listed quantity.'
        if self.unit_price is not None and self.unit_price <= Decimal('0'):
            errors['unit_price'] = 'Unit price must be greater than zero.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class MarketOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    listing = models.ForeignKey(
        MarketListing,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='market_orders',
    )
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    buyer_note = models.TextField(blank=True)
    seller_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status', '-created_at'], name='mb_order_buyer_status_idx'),
            models.Index(fields=['listing', 'status'], name='mb_order_listing_status_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_kg__gt=0),
                name='market_order_quantity_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gt=0),
                name='market_order_unit_price_positive',
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gt=0),
                name='market_order_total_price_positive',
            ),
        ]

    def clean(self):
        errors = {}

        if self.quantity_kg is not None and self.quantity_kg <= Decimal('0'):
            errors['quantity_kg'] = 'Quantity must be greater than zero.'
        if self.listing_id and self.quantity_kg and self.quantity_kg > self.listing.available_quantity_kg:
            errors['quantity_kg'] = 'Requested quantity is not available.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Order #{self.pk or "new"} for {self.listing}'
