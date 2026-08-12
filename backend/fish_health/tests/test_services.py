from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.models import Notification
from fish_health.models import DiseaseProfile, HealthRecord
from fish_health.services.core.alerts import create_health_notifications
from fish_health.services.core.diagnosis import (
    calculate_record_severity,
    find_environment_matches,
    match_possible_diseases,
)
from ponds.models import Pond


class FishHealthServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='health-service-user', password='pass',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='Diagnosis Pond',
            location='Natore',
            area_decimal=Decimal('20.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=1000,
        )
        self.disease = DiseaseProfile.objects.create(
            name='Gill Stress',
            species=['Rui'],
            symptoms=['gasping at surface', 'red gills'],
            description='A fish health issue.',
            risk_level=DiseaseProfile.RiskLevel.HIGH,
            recommended_treatments=['Improve aeration.'],
            environmental_triggers=['low dissolved oxygen'],
        )

    def build_record(self, **overrides):
        values = {
            'pond': self.pond,
            'created_by': self.user,
            'observed_at': timezone.make_aware(datetime(2026, 8, 1)),
            'species': 'Rui',
            'symptoms': ['gasping at surface'],
            'symptom_notes': '',
            'affected_count': 4,
            'mortality_count': 0,
            'severity': HealthRecord.Severity.MODERATE,
        }
        values.update(overrides)
        return HealthRecord.objects.create(**values)

    def test_matching_considers_symptoms_and_environment(self):
        matches = match_possible_diseases(
            species='Rui',
            symptoms=['gasping at surface'],
            symptom_notes='',
            water_quality_snapshot={'dissolved_oxygen': 3.5},
            weather_snapshot={},
        )

        match = next(item for item in matches if item['name'] == 'Gill Stress')
        self.assertIn('gasping at surface', match['matched_symptoms'])
        self.assertIn('low dissolved oxygen', match['environment_matches'])

    def test_severity_is_critical_for_mortality_and_high_for_high_risk_terms(self):
        critical = self.build_record(mortality_count=1)
        high = self.build_record(symptoms=['red gills'])

        self.assertEqual(calculate_record_severity(critical, []), HealthRecord.Severity.CRITICAL)
        self.assertEqual(calculate_record_severity(high, []), HealthRecord.Severity.HIGH)

    def test_environment_matches_report_water_and_weather_risks(self):
        matches = find_environment_matches(
            ['low dissolved oxygen', 'cloudy weather'],
            {'dissolved_oxygen': 4},
            {'disease_risk': 'High'},
        )

        self.assertEqual(matches, ['low dissolved oxygen', 'weather disease risk'])

    def test_health_notifications_are_deduplicated_when_unread(self):
        record = self.build_record(
            severity=HealthRecord.Severity.HIGH,
            possible_diseases=[{'name': 'Gill Stress'}],
            ai_recommendation='Improve aeration.',
        )

        first = create_health_notifications(record)
        second = create_health_notifications(record)

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        self.assertEqual(Notification.objects.filter(parameter='Fish health').count(), 1)
