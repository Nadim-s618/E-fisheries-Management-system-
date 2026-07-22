from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Pond
from .serializers import PondSerializer


def user_ponds(user):
    if user.is_staff:
        return Pond.objects.select_related('owner').all()
    return Pond.objects.select_related('owner').filter(owner=user)


def get_user_pond(user, pk):
    return user_ponds(user).filter(pk=pk).first()


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def pond_list(request):
    if request.method == 'GET':
        serializer = PondSerializer(user_ponds(request.user), many=True)
        return Response(serializer.data)

    serializer = PondSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    pond = serializer.save(owner=request.user)
    return Response(PondSerializer(pond).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def pond_detail(request, pk):
    pond = get_user_pond(request.user, pk)
    if not pond:
        return Response({'detail': 'Pond not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(PondSerializer(pond).data)

    if request.method == 'DELETE':
        pond.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PondSerializer(
        pond,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request},
    )
    serializer.is_valid(raise_exception=True)
    pond = serializer.save()
    return Response(PondSerializer(pond).data)
