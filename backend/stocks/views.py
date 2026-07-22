from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ponds.views import get_user_pond

from .models import FishStock
from .serializers import FishStockSerializer


def user_stocks(user):
    queryset = FishStock.objects.select_related('pond', 'pond__owner').prefetch_related('growth_records')
    if user.is_staff:
        return queryset.all()
    return queryset.filter(pond__owner=user)


def get_user_stock(user, pk):
    return user_stocks(user).filter(pk=pk).first()


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def stock_list(request, pond_pk):
    pond = get_user_pond(request.user, pond_pk)
    if not pond:
        return Response({'detail': 'Pond not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        stocks = pond.stocks.prefetch_related('growth_records').all()
        serializer = FishStockSerializer(stocks, many=True)
        return Response(serializer.data)

    serializer = FishStockSerializer(
        data=request.data,
        context={'request': request, 'pond': pond},
    )
    serializer.is_valid(raise_exception=True)
    stock = serializer.save(pond=pond)
    return Response(FishStockSerializer(stock).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def stock_detail(request, pk):
    stock = get_user_stock(request.user, pk)
    if not stock:
        return Response({'detail': 'Stock not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(FishStockSerializer(stock).data)

    if request.method == 'DELETE':
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = FishStockSerializer(
        stock,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request, 'pond': stock.pond},
    )
    serializer.is_valid(raise_exception=True)
    stock = serializer.save()
    return Response(FishStockSerializer(stock).data)
