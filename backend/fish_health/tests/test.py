from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from fish_health.models import DiseaseProfile, HealthRecord, TreatmentPlan, TreatmentTrackingEntry
from ponds.models import Pond


BASE_URL = '/api/fish-health/'


class FishHealthAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username='health-api-owner', password='pass',
        )
        self.other_user = user_model.objects.create_user(
            username='health-api-other', password='pass',
        )
        self.pond = self.create_pond(self.owner, 'Owner Pond')
        self.other_pond = self.create_pond(self.other_user, 'Other Pond')
        self.disease = DiseaseProfile.objects.create(
            name='API Ich',
            species=['Rui'],
            symptoms=['white spots'],
            description='Parasite profile.',
            risk_level=DiseaseProfile.RiskLevel.MODERATE,
            recommended_treatments=['Improve water quality.'],
        )

    def create_pond(self, owner, name):
        return Pond.objects.create(
            owner=owner,
            name=name,
            location='Natore',
            area_decimal=Decimal('20.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=1000,
        )

    def authenticate(self, user=None):
        self.client.force_authenticate(user or self.owner)

    def record_payload(self, **overrides):
        payload = {
            'pond': self.pond.id,
            'observed_at': '2026-08-01T10:00:00Z',
            'species': 'Rui',
            'symptoms': ['white spots'],
            'symptom_notes': 'Fish are rubbing against the pond wall.',
            'affected_count': 5,
            'mortality_count': 0,
            'status': HealthRecord.Status.OPEN,
        }
        payload.update(overrides)
        return payload

    def treatment_payload(self, **overrides):
        payload = {
            'pond': self.pond.id,
            'medicine_name': 'Salt bath',
            'dosage': '10 g/L',
            'start_date': '2026-08-01',
            'cost': '250.00',
            'status': TreatmentPlan.Status.PLANNED,
        }
        payload.update(overrides)
        return payload

    def test_health_endpoints_require_authentication(self):
        for path in ('diseases/', 'health-records/', 'treatments/', 'dashboard/', 'recommendation/', 'alerts/'):
            self.assertEqual(self.client.get(BASE_URL + path).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_disease_library_supports_search_and_risk_filters(self):
        self.authenticate()

        response = self.client.get(BASE_URL + 'diseases/?search=API&risk=Moderate')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'API Ich')

    @patch('fish_health.serializers.get_latest_weather_snapshot', return_value={})
    @patch('fish_health.serializers.get_latest_water_quality_snapshot', return_value={})
    def test_create_health_record_diagnoses_and_scopes_to_owner(self, mock_water, mock_weather):
        self.authenticate()

        response = self.client.post(BASE_URL + 'health-records/', self.record_payload(), format='json')
        other_response = self.client.post(
            BASE_URL + 'health-records/', self.record_payload(pond=self.other_pond.id), format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_by_name'], '')
        self.assertEqual(response.data['severity'], HealthRecord.Severity.HIGH)
        self.assertTrue(response.data['possible_diseases'])
        self.assertEqual(response.data['water_quality_snapshot'], {})
        self.assertEqual(other_response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_water.assert_called()
        mock_weather.assert_called()

    def test_health_record_requires_symptoms_or_notes(self):
        self.authenticate()

        response = self.client.post(
            BASE_URL + 'health-records/', self.record_payload(symptoms=[], symptom_notes=' '), format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_counts_records_and_active_treatments(self):
        self.authenticate()
        record = HealthRecord.objects.create(
            pond=self.pond,
            created_by=self.owner,
            observed_at=timezone.now(),
            species='Rui',
            symptoms=['white spots'],
            severity=HealthRecord.Severity.CRITICAL,
        )
        TreatmentPlan.objects.create(
            pond=self.pond,
            created_by=self.owner,
            medicine_name='Salt bath',
            dosage='10 g/L',
            start_date=date.today(),
            status=TreatmentPlan.Status.ACTIVE,
        )

        response = self.client.get(BASE_URL + 'dashboard/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['total_records'], 1)
        self.assertEqual(response.data['summary']['critical_cases'], 1)
        self.assertEqual(response.data['summary']['active_treatments'], 1)
        self.assertEqual(response.data['latest_records'][0]['id'], record.id)

    def test_create_treatment_adds_tracking_entry_and_tracking_endpoint_can_update_status(self):
        self.authenticate()
        response = self.client.post(BASE_URL + 'treatments/', self.treatment_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        treatment_id = response.data['id']
        self.assertEqual(len(response.data['tracking']), 1)
        self.assertEqual(response.data['tracking'][0]['status'], TreatmentPlan.Status.PLANNED)

        tracking = self.client.post(
            f'{BASE_URL}treatments/{treatment_id}/tracking/',
            {'status': TreatmentPlan.Status.ACTIVE, 'administered_dosage': '10 g/L'},
            format='json',
        )

        self.assertEqual(tracking.status_code, status.HTTP_201_CREATED)
        treatment = TreatmentPlan.objects.get(pk=treatment_id)
        self.assertEqual(treatment.status, TreatmentPlan.Status.ACTIVE)
        self.assertEqual(treatment.tracking_entries.count(), 2)

    @patch('financials.services.create_automatic_financial_record')
    def test_completing_paid_treatment_creates_financial_record(self, mock_financial):
        self.authenticate()
        response = self.client.post(
            BASE_URL + 'treatments/',
            self.treatment_payload(status=TreatmentPlan.Status.COMPLETED, end_date='2026-08-05'),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_financial.assert_called_once()
        self.assertEqual(mock_financial.call_args.args[1]['amount'], Decimal('250.00'))

    def test_recommendation_is_empty_state_when_no_records_exist(self):
        self.authenticate()

        response = self.client.get(BASE_URL + 'recommendation/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['record'])
        self.assertIn('Create a health record', response.data['recommendation'])

    def test_alerts_can_be_marked_read(self):
        self.authenticate()
        record = HealthRecord.objects.create(
            pond=self.pond,
            created_by=self.owner,
            observed_at=timezone.now(),
            severity=HealthRecord.Severity.HIGH,
            possible_diseases=[{'name': 'API Ich'}],
            ai_recommendation='Monitor closely.',
        )
        from fish_health.services.core.alerts import create_health_notifications
        create_health_notifications(record)

        response = self.client.post(BASE_URL + 'alerts/', {'ids': 'all'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.owner.notifications.filter(parameter='Fish health', is_read=False).exists())
