from django.db.models import Avg, F, Window
from django.db.models.functions import RowNumber, TruncDate, TruncMonth, TruncWeek, TruncYear
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ponds.models import Pond
from feeding.models import FeedingRecommendation
from growth.models import GrowthRecord
from stocks.models import FishStock
from weather.models import WeatherReport

from .models import WaterQualityReading
from .serializers import WaterQualityReadingSerializer
from .services.ai_advisor import get_water_quality_advice
from .services.analyser import analyse_water_quality, get_primary_species
from .services.notification_service import create_water_quality_notifications
from .utils.thresholds import STATUS_DANGER, STATUS_GOOD, STATUS_WARNING
from .utils.trends import calculate_trends


PERIOD_TRUNCATORS = {
    'daily': TruncDate('created_at'),
    'weekly': TruncWeek('created_at'),
    'monthly': TruncMonth('created_at'),
    'yearly': TruncYear('created_at'),
}


class WaterQualityReadingViewSet(viewsets.ModelViewSet):
    serializer_class = WaterQualityReadingSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = WaterQualityReading.objects.select_related('pond', 'pond__owner').order_by('-created_at')
        user = self.request.user

        if not user.is_staff:
            queryset = queryset.filter(pond__owner=user)

        return self.apply_filters(queryset)

    def perform_create(self, serializer):
        reading = serializer.save()
        create_water_quality_notifications(reading)

    def apply_filters(self, queryset):
        pond_id = self.request.query_params.get('pond')
        date = self.request.query_params.get('date')
        status = self.request.query_params.get('status')

        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            queryset = queryset.filter(pond_id=pond_id)

        if date:
            parsed_date = parse_date(date)
            if parsed_date is None:
                raise ValidationError({'date': 'Date must use YYYY-MM-DD format.'})
            queryset = queryset.filter(created_at__date=parsed_date)

        if status:
            valid_statuses = {
                choice[0]
                for choice in WaterQualityReading.OverallStatus.choices
            }
            if status not in valid_statuses:
                raise ValidationError({
                    'status': f'Status must be one of: {", ".join(sorted(valid_statuses))}.',
                })
            queryset = queryset.filter(overall_status=status)

        return queryset


class WaterQualityDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pond_id = request.query_params.get('pond')

        if not pond_id:
            return Response(
                {'pond': 'This query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not pond_id.isdigit():
            return Response(
                {'pond': 'Pond must be a valid numeric id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        readings = WaterQualityReading.objects.select_related('pond', 'pond__owner').filter(
            pond_id=pond_id,
        ).order_by('-created_at')

        if not request.user.is_staff:
            readings = readings.filter(pond__owner=request.user)

        latest_reading = readings.first()
        if latest_reading is None:
            return Response(
                {'detail': 'No water quality reading found for this pond.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        previous_reading = readings.exclude(pk=latest_reading.pk).first()
        analysis = analyse_water_quality(
            temperature=latest_reading.temperature,
            ph=latest_reading.ph,
            dissolved_oxygen=latest_reading.dissolved_oxygen,
            ammonia=latest_reading.ammonia,
            nitrite=latest_reading.nitrite,
            nitrate=latest_reading.nitrate,
            turbidity=latest_reading.turbidity,
            salinity=latest_reading.salinity,
            water_level=latest_reading.water_level,
            species=get_primary_species(latest_reading.pond),
        )
        trends = calculate_trends(latest_reading, previous_reading)
        parameter_cards = [
            {
                'parameter': parameter['parameter'],
                'current_value': parameter['value'],
                'normal_range': parameter['normal_range'],
                'status': parameter['status'],
                'trend': trends[parameter['parameter']],
                'last_updated': latest_reading.updated_at.isoformat(),
            }
            for parameter in analysis['parameters']
        ]

        return Response({
            'latest_reading': WaterQualityReadingSerializer(latest_reading).data,
            'parameter_cards': parameter_cards,
            'strategy': analysis['strategy'],
            'overall_status': analysis['overall_status'],
            'danger_count': self.count_status(parameter_cards, STATUS_DANGER),
            'warning_count': self.count_status(parameter_cards, STATUS_WARNING),
            'good_count': self.count_status(parameter_cards, STATUS_GOOD),
            'ai_advice': get_water_quality_advice(
                analysis,
                self.build_advisor_context(latest_reading, readings),
            ),
        })

    def count_status(self, parameter_cards, status_name):
        return sum(
            1
            for parameter in parameter_cards
            if parameter['status'] == status_name
        )

    def build_advisor_context(self, latest_reading, readings):
        pond = latest_reading.pond
        active_stocks = FishStock.objects.filter(
            pond=pond,
            status=FishStock.Status.ACTIVE,
            current_quantity__gt=0,
        )
        latest_growth = (
            GrowthRecord.objects
            .filter(stock__in=active_stocks)
            .order_by('-recorded_date', '-id')
            .first()
        )
        latest_weather = (
            WeatherReport.objects
            .filter(pond=pond)
            .order_by('-observed_at', '-created_at')
            .first()
        )
        latest_feeding = (
            FeedingRecommendation.objects
            .filter(pond=pond)
            .order_by('-recommendation_date', '-created_at')
            .first()
        )

        return {
            'pond': {
                'name': pond.name,
                'location': pond.location,
                'area_decimal': str(pond.area_decimal),
                'average_depth_ft': str(pond.average_depth_ft),
                'water_source': pond.water_source,
                'stocking_capacity': pond.stocking_capacity,
            },
            'stock': {
                'active_batches': active_stocks.count(),
                'current_quantity': sum(stock.current_quantity for stock in active_stocks),
                'latest_average_weight_g': str(latest_growth.average_weight_g) if latest_growth else None,
                'latest_growth_date': latest_growth.recorded_date.isoformat() if latest_growth else None,
            },
            'weather': {
                'fish_weather_risk': latest_weather.fish_weather_risk if latest_weather else None,
                'disease_risk': latest_weather.disease_risk if latest_weather else None,
                'air_temperature': latest_weather.air_temperature if latest_weather else None,
                'rainfall_probability': latest_weather.rainfall_probability if latest_weather else None,
            },
            'feeding': {
                'recommended_feed_kg': str(latest_feeding.recommended_feed_kg) if latest_feeding else None,
                'meals': latest_feeding.meals if latest_feeding else None,
                'status': latest_feeding.status if latest_feeding else None,
            },
            'recent_reading_count': readings.count(),
        }


class WaterQualityHistoricalBaseView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        period = request.query_params.get('period', 'daily').lower()

        if period not in PERIOD_TRUNCATORS:
            return Response(
                {'period': 'Period must be one of: daily, weekly, monthly, yearly.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_filtered_queryset(request)
        results = self.get_aggregated_results(queryset, period)

        return Response({
            'period': period,
            'results': results,
        })

    def get_filtered_queryset(self, request):
        queryset = WaterQualityReading.objects.all()
        pond_id = request.query_params.get('pond')

        if not request.user.is_staff:
            queryset = queryset.filter(pond__owner=request.user)

        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            queryset = queryset.filter(pond_id=pond_id)

        return queryset

    def get_aggregated_results(self, queryset, period):
        rows = (
            queryset
            .annotate(period_date=PERIOD_TRUNCATORS[period])
            .values('period_date')
            .annotate(
                temperature=Avg('temperature'),
                ph=Avg('ph'),
                dissolved_oxygen=Avg('dissolved_oxygen'),
                ammonia=Avg('ammonia'),
                nitrite=Avg('nitrite'),
                nitrate=Avg('nitrate'),
                turbidity=Avg('turbidity'),
                salinity=Avg('salinity'),
                water_level=Avg('water_level'),
            )
            .order_by('period_date')
        )

        return [self.format_row(row) for row in rows]

    def format_row(self, row):
        return {
            'date': row['period_date'].date().isoformat() if hasattr(row['period_date'], 'date') else row['period_date'].isoformat(),
            'temperature': self.round_value(row['temperature']),
            'ph': self.round_value(row['ph']),
            'dissolved_oxygen': self.round_value(row['dissolved_oxygen']),
            'ammonia': self.round_value(row['ammonia']),
            'nitrite': self.round_value(row['nitrite']),
            'nitrate': self.round_value(row['nitrate']),
            'turbidity': self.round_value(row['turbidity']),
            'salinity': self.round_value(row['salinity']),
            'water_level': self.round_value(row['water_level']),
        }

    def round_value(self, value):
        if value is None:
            return None

        return round(float(value), 2)


class WaterQualityHistoryView(WaterQualityHistoricalBaseView):
    pass


class WaterQualityGraphView(WaterQualityHistoricalBaseView):
    pass


class WaterQualityCompareView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        pond_ids = self.get_pond_ids(request)
        if len(pond_ids) < 2:
            return Response(
                {'ponds': 'Provide at least two pond ids to compare.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ponds = self.get_accessible_ponds(request, pond_ids)
        if len(ponds) != len(set(pond_ids)):
            return Response(
                {'ponds': 'One or more ponds were not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        readings = WaterQualityReading.objects.select_related('pond').filter(
            pond_id__in=pond_ids,
        )
        latest_by_pond = self.get_latest_readings(readings)
        averages_by_pond = self.get_average_values(readings)
        results = [
            self.build_pond_result(
                pond,
                latest_by_pond.get(pond.id),
                averages_by_pond.get(pond.id, {}),
            )
            for pond in ponds
        ]

        ranked_results = sorted(
            results,
            key=lambda result: (
                result['rank_score']['danger_count'],
                result['rank_score']['warning_count'],
                -result['rank_score']['good_count'],
                result['pond']['name'].lower(),
            ),
        )

        for index, result in enumerate(ranked_results, start=1):
            result['rank'] = index
            result.pop('rank_score')

        return Response({
            'ponds': ranked_results,
        })

    def get_pond_ids(self, request):
        raw_ids = []

        if request.query_params.get('ponds'):
            raw_ids.extend(request.query_params.get('ponds').split(','))

        if request.query_params.get('pond_ids'):
            raw_ids.extend(request.query_params.get('pond_ids').split(','))

        raw_ids.extend(request.query_params.getlist('pond'))
        pond_ids = []

        for raw_id in raw_ids:
            cleaned_id = raw_id.strip()
            if not cleaned_id:
                continue
            if not cleaned_id.isdigit():
                raise ValidationError({'ponds': 'Pond ids must be numeric.'})
            pond_ids.append(int(cleaned_id))

        return list(dict.fromkeys(pond_ids))

    def get_accessible_ponds(self, request, pond_ids):
        ponds = Pond.objects.filter(id__in=pond_ids).only('id', 'name')

        if not request.user.is_staff:
            ponds = ponds.filter(owner=request.user)

        return list(ponds)

    def get_latest_readings(self, readings):
        latest_readings = (
            readings
            .annotate(
                row_number=Window(
                    expression=RowNumber(),
                    partition_by=[F('pond_id')],
                    order_by=F('created_at').desc(),
                ),
            )
            .filter(row_number=1)
        )

        return {
            reading.pond_id: reading
            for reading in latest_readings
        }

    def get_average_values(self, readings):
        rows = readings.values('pond_id').annotate(
            temperature=Avg('temperature'),
            ph=Avg('ph'),
            dissolved_oxygen=Avg('dissolved_oxygen'),
            ammonia=Avg('ammonia'),
            nitrite=Avg('nitrite'),
            nitrate=Avg('nitrate'),
            turbidity=Avg('turbidity'),
            salinity=Avg('salinity'),
            water_level=Avg('water_level'),
        )

        return {
            row['pond_id']: {
                'temperature': self.round_value(row['temperature']),
                'ph': self.round_value(row['ph']),
                'dissolved_oxygen': self.round_value(row['dissolved_oxygen']),
                'ammonia': self.round_value(row['ammonia']),
                'nitrite': self.round_value(row['nitrite']),
                'nitrate': self.round_value(row['nitrate']),
                'turbidity': self.round_value(row['turbidity']),
                'salinity': self.round_value(row['salinity']),
                'water_level': self.round_value(row['water_level']),
            }
            for row in rows
        }

    def build_pond_result(self, pond, latest_reading, average_values):
        if latest_reading is None:
            return {
                'rank': None,
                'pond': {
                    'id': pond.id,
                    'name': pond.name,
                },
                'latest_reading': None,
                'average_values': average_values,
                'overall_status': None,
                'danger_count': 0,
                'warning_count': 0,
                'good_count': 0,
                'rank_score': {
                    'danger_count': 999,
                    'warning_count': 999,
                    'good_count': 0,
                },
            }

        analysis = analyse_water_quality(
            temperature=latest_reading.temperature,
            ph=latest_reading.ph,
            dissolved_oxygen=latest_reading.dissolved_oxygen,
            ammonia=latest_reading.ammonia,
            nitrite=latest_reading.nitrite,
            nitrate=latest_reading.nitrate,
            turbidity=latest_reading.turbidity,
            salinity=latest_reading.salinity,
            water_level=latest_reading.water_level,
            species=get_primary_species(latest_reading.pond),
        )
        danger_count = self.count_status(analysis['parameters'], STATUS_DANGER)
        warning_count = self.count_status(analysis['parameters'], STATUS_WARNING)
        good_count = self.count_status(analysis['parameters'], STATUS_GOOD)

        return {
            'rank': None,
            'pond': {
                'id': pond.id,
                'name': pond.name,
            },
            'latest_reading': WaterQualityReadingSerializer(latest_reading).data,
            'average_values': average_values,
            'overall_status': analysis['overall_status'],
            'danger_count': danger_count,
            'warning_count': warning_count,
            'good_count': good_count,
            'rank_score': {
                'danger_count': danger_count,
                'warning_count': warning_count,
                'good_count': good_count,
            },
        }

    def count_status(self, parameters, status_name):
        return sum(
            1
            for parameter in parameters
            if parameter['status'] == status_name
        )

    def round_value(self, value):
        if value is None:
            return None

        return round(float(value), 2)
