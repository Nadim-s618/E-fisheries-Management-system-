from decimal import Decimal

from rest_framework import serializers

from stocks.models import FishStock

from .models import MarketListing, MarketOrder, MarketProfile, make_transaction_code
from .services import recommend_price


class MarketProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    can_buy = serializers.BooleanField(read_only=True)
    can_sell = serializers.BooleanField(read_only=True)

    class Meta:
        model = MarketProfile
        fields = (
            'id',
            'role',
            'role_display',
            'can_buy',
            'can_sell',
            'is_approved',
            'business_name',
            'phone',
            'address',
            'profile_picture',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'can_buy', 'can_sell', 'is_approved', 'created_at', 'updated_at')


class MarketListingSerializer(serializers.ModelSerializer):
    seller_name = serializers.SerializerMethodField()
    fish_stock_label = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    order_count = serializers.IntegerField(read_only=True)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = MarketListing
        fields = (
            'id',
            'seller',
            'seller_name',
            'fish_stock',
            'fish_stock_label',
            'source_type',
            'source_type_display',
            'species',
            'average_height_cm',
            'average_weight_g',
            'title',
            'quantity_kg',
            'available_quantity_kg',
            'unit_price',
            'suggested_price',
            'total_value',
            'location',
            'available_from',
            'description',
            'photo',
            'photo_url',
            'status',
            'status_display',
            'order_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'seller',
            'seller_name',
            'fish_stock_label',
            'source_type_display',
            'total_value',
            'photo_url',
            'status_display',
            'order_count',
            'created_at',
            'updated_at',
        )
        extra_kwargs = {
            'photo': {'write_only': True, 'required': False},
            'available_quantity_kg': {'required': False},
            'suggested_price': {'required': False},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user.is_authenticated and not request.user.is_staff:
            self.fields['fish_stock'].queryset = FishStock.objects.filter(pond__owner=request.user)

    def get_seller_name(self, listing):
        return listing.seller.get_full_name() or listing.seller.username

    def get_fish_stock_label(self, listing):
        if not listing.fish_stock:
            return ''
        return f'{listing.fish_stock.batch_name} - {listing.fish_stock.species}'

    def get_photo_url(self, listing):
        if not listing.photo:
            return ''
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(listing.photo.url)
        return listing.photo.url

    def validate_quantity_kg(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

    def validate_available_quantity_kg(self, value):
        if value < Decimal('0'):
            raise serializers.ValidationError('Available quantity cannot be negative.')
        return value

    def validate_unit_price(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Unit price must be greater than zero.')
        return value

    def validate_average_height_cm(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Average height must be greater than zero.')
        return value

    def validate_average_weight_g(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Average weight must be greater than zero.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        seller = getattr(request, 'user', None)
        instance = self.instance
        source_type = attrs.get('source_type', getattr(instance, 'source_type', MarketListing.SourceType.MANUAL))
        fish_stock = attrs.get('fish_stock', getattr(instance, 'fish_stock', None))
        quantity = attrs.get('quantity_kg', getattr(instance, 'quantity_kg', None))
        available = attrs.get('available_quantity_kg', getattr(instance, 'available_quantity_kg', None))

        if source_type == MarketListing.SourceType.INVENTORY and not fish_stock:
            raise serializers.ValidationError({'fish_stock': 'Select a stock batch for inventory listings.'})
        if fish_stock and seller and not seller.is_staff and fish_stock.pond.owner_id != seller.id:
            raise serializers.ValidationError({'fish_stock': 'Fish stock not found.'})
        if quantity is not None and available is not None and available > quantity:
            raise serializers.ValidationError({'available_quantity_kg': 'Available quantity cannot exceed listed quantity.'})

        return attrs

    def create(self, validated_data):
        request = self.context['request']

        if not validated_data.get('available_quantity_kg'):
            validated_data['available_quantity_kg'] = validated_data['quantity_kg']
        if not validated_data.get('suggested_price'):
            suggestion = recommend_price(
                validated_data.get('species'),
                validated_data.get('location'),
                validated_data.get('quantity_kg'),
            )
            validated_data['suggested_price'] = Decimal(str(suggestion['suggested_price']))

        return MarketListing.objects.create(seller=request.user, **validated_data)


class MarketOrderSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_species = serializers.CharField(source='listing.species', read_only=True)
    listing_location = serializers.CharField(source='listing.location', read_only=True)
    seller = serializers.IntegerField(source='listing.seller_id', read_only=True)
    seller_name = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()
    buyer_username = serializers.SerializerMethodField()
    buyer_email = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketOrder
        fields = (
            'id',
            'listing',
            'listing_title',
            'listing_species',
            'listing_location',
            'seller',
            'seller_name',
            'buyer',
            'buyer_name',
            'buyer_username',
            'buyer_email',
            'quantity_kg',
            'unit_price',
            'total_price',
            'transaction_code',
            'status',
            'status_display',
            'buyer_full_name',
            'buyer_address',
            'buyer_contact_number',
            'buyer_note',
            'seller_note',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'buyer',
            'buyer_name',
            'unit_price',
            'total_price',
            'transaction_code',
            'status',
            'status_display',
            'seller_note',
            'created_at',
            'updated_at',
        )

    def get_seller_name(self, order):
        seller = order.listing.seller
        return seller.get_full_name() or seller.username

    def get_buyer_name(self, order):
        if order.buyer is None:
            return order.buyer_full_name or 'Guest buyer'
        return order.buyer.get_full_name() or order.buyer.username

    def get_buyer_username(self, order):
        return order.buyer.username if order.buyer else ''

    def get_buyer_email(self, order):
        return order.buyer.email if order.buyer else ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['listing'].queryset = MarketListing.objects.filter(
            status=MarketListing.Status.ACTIVE,
        )

    def validate_quantity_kg(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

    def validate_buyer_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Full name is required.')
        return value

    def validate_buyer_address(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Full address is required.')
        return value

    def validate_buyer_contact_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Contact number is required.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        listing = attrs.get('listing')
        quantity = attrs.get('quantity_kg')

        required_buyer_fields = {
            'buyer_full_name': 'Full name is required.',
            'buyer_address': 'Full address is required.',
            'buyer_contact_number': 'Contact number is required.',
        }
        if self.instance is None:
            missing_fields = {
                field: message
                for field, message in required_buyer_fields.items()
                if not str(attrs.get(field, '')).strip()
            }
            if missing_fields:
                raise serializers.ValidationError(missing_fields)

        if listing and listing.status != MarketListing.Status.ACTIVE:
            raise serializers.ValidationError({'listing': 'This listing is not available for orders.'})
        if listing and request and listing.seller_id == request.user.id:
            raise serializers.ValidationError({'listing': 'You cannot buy from your own listing.'})
        if listing and quantity and quantity > listing.available_quantity_kg:
            raise serializers.ValidationError({'quantity_kg': 'Requested quantity is not available.'})

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        listing = validated_data['listing']
        quantity = validated_data['quantity_kg']
        unit_price = listing.unit_price
        return MarketOrder.objects.create(
            buyer=request.user,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            **validated_data,
        )


class PublicOrderTrackingSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_species = serializers.CharField(source='listing.species', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MarketOrder
        fields = (
            'transaction_code',
            'listing_title',
            'listing_species',
            'quantity_kg',
            'total_price',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        )


class GuestMarketOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketOrder
        fields = (
            'listing',
            'quantity_kg',
            'buyer_full_name',
            'buyer_address',
            'buyer_contact_number',
            'buyer_note',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['listing'].queryset = MarketListing.objects.filter(
            status=MarketListing.Status.ACTIVE,
            seller__email__iexact='shahoriyernadim@gmail.com',
        )

    def validate_quantity_kg(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value

    def validate_buyer_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name is required.')
        return value

    def validate_buyer_address(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Address is required.')
        return value

    def validate_buyer_contact_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Mobile number is required.')
        return value

    def validate(self, attrs):
        listing = attrs.get('listing')
        quantity = attrs.get('quantity_kg')
        if listing and listing.status != MarketListing.Status.ACTIVE:
            raise serializers.ValidationError({'listing': 'This fish is no longer available.'})
        if listing and quantity and quantity > listing.available_quantity_kg:
            raise serializers.ValidationError({'quantity_kg': 'Requested quantity is not available.'})
        return attrs

    def create(self, validated_data):
        listing = validated_data['listing']
        quantity = validated_data['quantity_kg']
        unit_price = listing.unit_price
        transaction_code = make_transaction_code()
        return MarketOrder.objects.create(
            buyer=None,
            transaction_code=transaction_code,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            **validated_data,
        )


class GuestMarketCartItemSerializer(serializers.Serializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=MarketListing.objects.none())
    quantity_kg = serializers.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['listing'].queryset = MarketListing.objects.filter(
            status=MarketListing.Status.ACTIVE,
            seller__email__iexact='shahoriyernadim@gmail.com',
        )

    def validate_quantity_kg(self, value):
        if value <= Decimal('0'):
            raise serializers.ValidationError('Quantity must be greater than zero.')
        return value


class GuestMarketCartOrderSerializer(serializers.Serializer):
    items = GuestMarketCartItemSerializer(many=True, allow_empty=False)
    buyer_full_name = serializers.CharField(max_length=140)
    buyer_address = serializers.CharField(max_length=260)
    buyer_contact_number = serializers.CharField(max_length=40)
    buyer_note = serializers.CharField(required=False, allow_blank=True)

    def validate_buyer_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Name is required.')
        return value

    def validate_buyer_address(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Address is required.')
        return value

    def validate_buyer_contact_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Mobile number is required.')
        return value

    def validate_items(self, items):
        listing_ids = [item['listing'].id for item in items]
        if len(listing_ids) != len(set(listing_ids)):
            raise serializers.ValidationError('Each fish listing can only appear once in the cart.')
        for item in items:
            if item['quantity_kg'] > item['listing'].available_quantity_kg:
                raise serializers.ValidationError(
                    f"Not enough stock available for {item['listing'].title}."
                )
        return items

    def create(self, validated_data):
        items = validated_data.pop('items')
        orders = []
        transaction_code = make_transaction_code()
        for item in items:
            listing = MarketListing.objects.select_for_update().get(pk=item['listing'].pk)
            quantity = item['quantity_kg']
            if listing.status != MarketListing.Status.ACTIVE or quantity > listing.available_quantity_kg:
                raise serializers.ValidationError(
                    f"{listing.title} is no longer available in the requested quantity."
                )
            orders.append(MarketOrder.objects.create(
                listing=listing,
                buyer=None,
                transaction_code=transaction_code,
                quantity_kg=quantity,
                unit_price=listing.unit_price,
                total_price=quantity * listing.unit_price,
                **validated_data,
            ))
        return orders
