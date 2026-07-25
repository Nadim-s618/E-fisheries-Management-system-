from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ponds.models import Pond

from .serializers import WeatherReportSerializer
from .services.openweather import WeatherServiceError
from .services.reports import get_or_refresh_weather_report


class WeatherDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pond = self.get_pond(request)
        force_refresh = request.query_params.get('refresh') in {'1', 'true', 'yes'}

        try:
            report, is_stale, source_error = get_or_refresh_weather_report(
                pond,
                force_refresh=force_refresh,
            )
        except WeatherServiceError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({
            'report': WeatherReportSerializer(report).data,
            'stale': is_stale,
            'source_error': source_error,
        })

    def get_pond(self, request):
        pond_id = request.query_params.get('pond')
        if not pond_id:
            raise ValidationError({'pond': 'This query parameter is required.'})
        if not pond_id.isdigit():
            raise ValidationError({'pond': 'Pond must be a valid numeric id.'})

        queryset = Pond.objects.select_related('owner')
        if not request.user.is_staff:
            queryset = queryset.filter(owner=request.user)

        pond = queryset.filter(pk=pond_id).first()
        if not pond:
            raise ValidationError({'pond': 'Pond not found.'})

        return pond
