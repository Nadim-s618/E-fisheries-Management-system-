from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify
from market_bridge.models import MarketProfile
from rest_framework import serializers

from .models import Notification


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    market_profile = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'address',
            'profile_picture_url',
            'market_profile',
            'is_staff',
        )

    def get_full_name(self, user):
        return user.get_full_name() or user.username

    def get_address(self, user):
        profile = getattr(user, 'market_profile', None)
        return profile.address if profile else ''

    def get_profile_picture_url(self, user):
        profile = getattr(user, 'market_profile', None)
        if not profile or not profile.profile_picture:
            return ''
        request = self.context.get('request')
        return request.build_absolute_uri(profile.profile_picture.url) if request else profile.profile_picture.url

    def get_market_profile(self, user):
        profile = getattr(user, 'market_profile', None)
        if not profile:
            return {
                'role': 'both',
                'role_display': 'Buyer and seller',
                'can_buy': True,
                'can_sell': True,
                'is_approved': True,
            }
        return {
            'role': profile.role,
            'role_display': profile.get_role_display(),
            'can_buy': profile.can_buy,
            'can_sell': profile.can_sell,
            'is_approved': profile.is_approved,
        }


class SignupSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return email

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        full_name = validated_data['full_name'].strip()
        first_name, last_name = self._split_name(full_name)
        username = self._unique_username(validated_data['email'])

        return User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name,
        )

    def _split_name(self, full_name):
        parts = full_name.split(maxsplit=1)
        first_name = parts[0] if parts else ''
        last_name = parts[1] if len(parts) > 1 else ''
        return first_name, last_name

    def _unique_username(self, email):
        base_username = slugify(email.split('@')[0]) or 'user'
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            counter += 1
            username = f'{base_username}{counter}'

        return username


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email_or_username = attrs['email'].strip()
        password = attrs['password']
        username = email_or_username

        user_by_email = User.objects.filter(email__iexact=email_or_username).first()
        if user_by_email:
            username = user_by_email.username

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')

        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False)
    address = serializers.CharField(max_length=220, required=False, allow_blank=True)
    profile_picture = serializers.FileField(required=False, allow_null=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=False)
    confirm_password = serializers.CharField(write_only=True, min_length=8, required=False)

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.context['request'].user.pk).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return email

    def validate(self, attrs):
        if 'new_password' in attrs or 'confirm_password' in attrs:
            if attrs.get('new_password') != attrs.get('confirm_password'):
                raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
            validate_password(attrs['new_password'], self.context['request'].user)
        return attrs

    def update(self, user, validated_data):
        full_name = validated_data.pop('full_name', None)
        address = validated_data.pop('address', None)
        profile_picture = validated_data.pop('profile_picture', serializers.empty)
        new_password = validated_data.pop('new_password', None)
        validated_data.pop('confirm_password', None)

        if full_name is not None:
            parts = full_name.strip().split(maxsplit=1)
            user.first_name = parts[0] if parts else ''
            user.last_name = parts[1] if len(parts) > 1 else ''
        for field, value in validated_data.items():
            setattr(user, field, value)
        if new_password:
            user.set_password(new_password)
        user.save()

        profile, _ = MarketProfile.objects.get_or_create(user=user)
        if address is not None:
            profile.address = address.strip()
        if profile_picture is not serializers.empty:
            profile.profile_picture = profile_picture
        profile.save()
        return user


class NotificationSerializer(serializers.ModelSerializer):
    pond_name = serializers.CharField(source='pond.name', read_only=True)

    class Meta:
        model = Notification
        fields = (
            'id',
            'pond',
            'pond_name',
            'parameter',
            'current_value',
            'reason',
            'priority',
            'is_read',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields
