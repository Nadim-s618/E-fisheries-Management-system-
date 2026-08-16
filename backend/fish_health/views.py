from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Notification
from ponds.models import Pond

from .models import DiseaseProfile, HealthRecord, TreatmentPlan, TreatmentTrackingEntry
from .serializers import (
    DiseaseProfileSerializer,
    HealthAlertSerializer,
    HealthRecordSerializer,
    TreatmentPlanSerializer,
    TreatmentTrackingSerializer,
)
from .services.core.diagnosis import diagnose_health_record
from .services.water_quality.context import get_latest_water_quality_snapshot, get_water_quality_risk_notes
from .services.weather.context import get_latest_weather_snapshot, get_weather_risk_notes


def user_ponds(user):
    if user.is_staff:
        return Pond.objects.select_related('owner').all()
    return Pond.objects.select_related('owner').filter(owner=user)


class DiseaseProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiseaseProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = DiseaseProfile.objects.filter(is_active=True)
        search = self.request.query_params.get('search')
        risk = self.request.query_params.get('risk')

        if search:
            queryset = queryset.filter(name__icontains=search)
        if risk:
            queryset = queryset.filter(risk_level=risk)

        return queryset.order_by('name')


class HealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = HealthRecord.objects.select_related(
            'pond',
            'pond__owner',
            'fish_stock',
            'created_by',
        )

        if not self.request.user.is_staff:
            queryset = queryset.filter(pond__owner=self.request.user)

        pond_id = self.request.query_params.get('pond')
        status_filter = self.request.query_params.get('status')

        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            queryset = queryset.filter(pond_id=pond_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'], url_path='rediagnose')
    def rediagnose(self, request, pk=None):
        record = diagnose_health_record(self.get_object())
        return Response(self.get_serializer(record).data)


class TreatmentPlanViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentPlanSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = TreatmentPlan.objects.select_related(
            'pond',
            'pond__owner',
            'fish_stock',
            'health_record',
            'disease',
            'created_by',
        )

        if not self.request.user.is_staff:
            queryset = queryset.filter(pond__owner=self.request.user)

        pond_id = self.request.query_params.get('pond')
        status_filter = self.request.query_params.get('status')

        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            queryset = queryset.filter(pond_id=pond_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        treatment = serializer.save()
        TreatmentTrackingEntry.objects.create(
            treatment=treatment,
            status=treatment.status,
            recorded_by=self.request.user,
            notes='Treatment plan created.',
        )
        self._create_completed_treatment_expense(treatment)

    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        treatment = serializer.save()
        if previous_status != treatment.status:
            TreatmentTrackingEntry.objects.create(
                treatment=treatment,
                status=treatment.status,
                recorded_by=self.request.user,
                notes=f'Status changed from {previous_status} to {treatment.status}.',
            )
        self._create_completed_treatment_expense(treatment)

    @action(detail=True, methods=['get', 'post'], url_path='tracking')
    def tracking(self, request, pk=None):
        treatment = self.get_object()
        if request.method == 'GET':
            entries = treatment.tracking_entries.select_related('recorded_by').all()
            return Response(TreatmentTrackingSerializer(entries, many=True).data)

        serializer = TreatmentTrackingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            entry = serializer.save(treatment=treatment, recorded_by=request.user)
            if treatment.status != entry.status:
                treatment.status = entry.status
                treatment.save(update_fields=['status', 'updated_at'])
            self._create_completed_treatment_expense(treatment)
        return Response(TreatmentTrackingSerializer(entry).data, status=status.HTTP_201_CREATED)

    def _create_completed_treatment_expense(self, treatment):
        if treatment.status != TreatmentPlan.Status.COMPLETED or treatment.cost <= 0:
            return

        from financials.services import create_automatic_financial_record

        create_automatic_financial_record(treatment.pond.owner, {
            'source_type': 'medicine_treatment',
            'source_id': treatment.id,
            'pond': treatment.pond_id,
            'fish_stock': treatment.fish_stock_id,
            'title': f'Treatment: {treatment.medicine_name}',
            'amount': treatment.cost,
            'transaction_date': treatment.end_date or timezone.localdate(),
            'reference': f'Treatment plan #{treatment.id}',
        })


class HealthDashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ponds = user_ponds(request.user)
        records = HealthRecord.objects.filter(pond__in=ponds)
        treatments = TreatmentPlan.objects.filter(pond__in=ponds)
        pond = self.get_pond(request, ponds)

        if pond is not None:
            records = records.filter(pond=pond)
            treatments = treatments.filter(pond=pond)

        active_statuses = [
            HealthRecord.Status.OPEN,
            HealthRecord.Status.MONITORING,
            HealthRecord.Status.TREATMENT,
        ]
        active_treatment_statuses = [
            TreatmentPlan.Status.PLANNED,
            TreatmentPlan.Status.ACTIVE,
        ]
        latest_records = records.select_related('pond', 'fish_stock', 'created_by')[:5]
        water_snapshot = get_latest_water_quality_snapshot(pond) if pond else {}
        weather_snapshot = get_latest_weather_snapshot(pond) if pond else {}

        return Response({
            'summary': {
                'total_records': records.count(),
                'active_cases': records.filter(status__in=active_statuses).count(),
                'critical_cases': records.filter(severity=HealthRecord.Severity.CRITICAL).count(),
                'active_treatments': treatments.filter(status__in=active_treatment_statuses).count(),
                'disease_library_count': DiseaseProfile.objects.filter(is_active=True).count(),
                'unread_health_alerts': self.health_alerts(request.user, pond).filter(is_read=False).count(),
            },
            'severity_breakdown': self.breakdown(records, 'severity'),
            'status_breakdown': self.breakdown(records, 'status'),
            'latest_records': HealthRecordSerializer(latest_records, many=True).data,
            'water_quality': {
                'snapshot': water_snapshot,
                'risk_notes': get_water_quality_risk_notes(water_snapshot),
            },
            'weather': {
                'snapshot': weather_snapshot,
                'risk_notes': get_weather_risk_notes(weather_snapshot),
            },
        })

    def get_pond(self, request, ponds):
        pond_id = request.query_params.get('pond')
        if not pond_id:
            return None
        if not pond_id.isdigit():
            raise ValidationError({'pond': 'Pond must be a valid numeric id.'})

        pond = ponds.filter(pk=pond_id).first()
        if pond is None:
            raise ValidationError({'pond': 'Pond not found.'})

        return pond

    def breakdown(self, queryset, field):
        return {
            row[field]: row['count']
            for row in queryset.values(field).annotate(count=Count('id'))
        }

    def health_alerts(self, user, pond=None):
        queryset = Notification.objects.filter(user=user, parameter='Fish health')
        if pond:
            queryset = queryset.filter(pond=pond)
        return queryset


class HealthRecommendationView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        records = HealthRecord.objects.select_related('pond', 'fish_stock', 'created_by')
        if not request.user.is_staff:
            records = records.filter(pond__owner=request.user)

        pond_id = request.query_params.get('pond')
        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            records = records.filter(pond_id=pond_id)

        record = records.first()
        if record is None:
            return Response({
                'recommendation': 'Create a health record with symptoms to generate AI health recommendations.',
                'record': None,
            })

        return Response({
            'recommendation': record.ai_recommendation,
            'record': HealthRecordSerializer(record).data,
        })


class HealthAlertsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        queryset = Notification.objects.select_related('pond').filter(
            user=request.user,
            parameter='Fish health',
        )
        pond_id = request.query_params.get('pond')

        if pond_id:
            if not pond_id.isdigit():
                raise ValidationError({'pond': 'Pond must be a valid numeric id.'})
            queryset = queryset.filter(pond_id=pond_id)

        serializer = HealthAlertSerializer(queryset[:30], many=True)
        return Response(serializer.data)

    def post(self, request):
        ids = request.data.get('ids', [])
        if ids == 'all':
            Notification.objects.filter(user=request.user, parameter='Fish health').update(is_read=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        Notification.objects.filter(
            user=request.user,
            parameter='Fish health',
            id__in=ids,
        ).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
