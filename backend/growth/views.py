from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from stocks.views import get_user_stock

from .models import GrowthRecord
from .serializers import GrowthRecordSerializer


def user_growth_records(user):
    queryset = GrowthRecord.objects.select_related(
        'stock',
        'stock__pond',
        'stock__pond__owner',
    )
    if user.is_staff:
        return queryset.all()
    return queryset.filter(stock__pond__owner=user)


def get_user_growth_record(user, pk):
    return user_growth_records(user).filter(pk=pk).first()


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def growth_list(request, stock_pk):
    stock = get_user_stock(request.user, stock_pk)
    if not stock:
        return Response({'detail': 'Stock not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = GrowthRecordSerializer(stock.growth_records.all(), many=True)
        return Response(serializer.data)

    serializer = GrowthRecordSerializer(
        data=request.data,
        context={'request': request, 'stock': stock},
    )
    serializer.is_valid(raise_exception=True)
    growth_record = serializer.save(stock=stock)
    return Response(GrowthRecordSerializer(growth_record).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def growth_detail(request, pk):
    growth_record = get_user_growth_record(request.user, pk)
    if not growth_record:
        return Response({'detail': 'Growth record not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(GrowthRecordSerializer(growth_record).data)

    if request.method == 'DELETE':
        growth_record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = GrowthRecordSerializer(
        growth_record,
        data=request.data,
        partial=request.method == 'PATCH',
        context={'request': request, 'stock': growth_record.stock},
    )
    serializer.is_valid(raise_exception=True)
    growth_record = serializer.save()
    return Response(GrowthRecordSerializer(growth_record).data)
