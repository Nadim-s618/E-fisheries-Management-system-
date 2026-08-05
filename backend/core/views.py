from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .content import HOMEPAGE_CONTENT
from .models import Notification
from .serializers import LoginSerializer, NotificationSerializer, SignupSerializer, UserSerializer
from .services.farm_advisor import get_farm_advice
from ponds.models import Pond


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications(request):
    queryset = Notification.objects.select_related('pond').filter(user=request.user)

    unread = request.query_params.get('unread')
    if unread in {'1', 'true', 'yes'}:
        queryset = queryset.filter(is_read=False)

    try:
        limit = int(request.query_params.get('limit', 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 50))

    serializer = NotificationSerializer(queryset[:limit], many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_advisor(request):
    pond_id = request.query_params.get('pond')
    if not pond_id:
        return Response({'pond': 'This query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
    if not pond_id.isdigit():
        return Response({'pond': 'Pond must be a valid numeric id.'}, status=status.HTTP_400_BAD_REQUEST)

    ponds = Pond.objects.all() if request.user.is_staff else Pond.objects.filter(owner=request.user)
    pond = ponds.filter(pk=pond_id).first()
    if pond is None:
        return Response({'pond': 'Pond not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(get_farm_advice(pond))


@api_view(['PATCH', 'POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    notification = Notification.objects.filter(pk=pk, user=request.user).first()
    if notification is None:
        return Response({'detail': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

    notification.is_read = True
    notification.save(update_fields=['is_read', 'updated_at'])
    return Response(NotificationSerializer(notification).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response(status=status.HTTP_204_NO_CONTENT)
