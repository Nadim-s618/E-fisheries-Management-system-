from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import LoginSerializer, SignupSerializer, UserSerializer


HOMEPAGE_CONTENT = {
    'navLinks': ['Features', 'Dashboard', 'About', 'Contact'],
    'hero': {
        'eyebrow': 'E-Fisheries Management System',
        'title': 'Smarter aquaculture, pond to market.',
        'accent': 'pond to market.',
        'subtitle': (
            'Monitor water quality, manage feeding schedules, track fish health, '
            'and connect with buyers - all from one platform built for modern fishery operations.'
        ),
    },
    'stats': [
        {'value': '1,200+', 'label': 'Active ponds managed'},
        {'value': '98%', 'label': 'Uptime reliability'},
        {'value': '40%', 'label': 'Reduction in feed waste'},
        {'value': '5 roles', 'label': 'From farmers to investors'},
    ],
    'features': [
        {
            'icon': 'water',
            'title': 'Water Quality Monitoring',
            'desc': 'Track pH, dissolved oxygen, temperature, and salinity in real time across all ponds.',
        },
        {
            'icon': 'feed',
            'title': 'Fish Feeding Management',
            'desc': 'Schedule and log feeding cycles. Monitor feed consumption and optimize nutrition per species.',
        },
        {
            'icon': 'growth',
            'title': 'Stock & Growth Tracking',
            'desc': 'Record harvest weight, mortality rates, and growth benchmarks across your full stock.',
        },
        {
            'icon': 'health',
            'title': 'Health & Disease Management',
            'desc': 'Log disease incidents, track treatments, and receive alerts for abnormal health patterns.',
        },
        {
            'icon': 'weather',
            'title': 'Weather Monitoring',
            'desc': 'Correlate local weather data with pond conditions to anticipate environmental stress.',
        },
        {
            'icon': 'finance',
            'title': 'Financial Management',
            'desc': 'Track operating costs, revenue from sales, and generate profit/loss reports per season.',
        },
        {
            'icon': 'market',
            'title': 'Market Analysis',
            'desc': 'Monitor fish market prices, demand trends, and seasonal forecasts to maximize your selling profit.',
        },
        {
            'icon': 'bridge',
            'title': 'Market Bridge',
            'desc': 'Connect directly with verified buyers, distributors, and exporters to sell your harvest faster.',
        },
    ],
    'cta': {
        'title': 'Ready to modernize your fishery?',
        'subtitle': 'Join fisheries managers, farmers, and investors already using E-Fisheries.',
        'buttonText': 'Start for free',
    },
}


def auth_payload(user, token):
    return {
        'token': token.key,
        'user': UserSerializer(user).data,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def homepage(request):
    return Response(HOMEPAGE_CONTENT)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(auth_payload(user, token), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)
    return Response(auth_payload(user, token))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({'user': UserSerializer(request.user).data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
