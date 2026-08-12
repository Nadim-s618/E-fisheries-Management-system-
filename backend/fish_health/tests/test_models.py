from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from fish_health.models import DiseaseProfile, HealthRecord, TreatmentPlan
from ponds.models import Pond


class FishHealthModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='health-model-user', password='pass',
        )
        self.pond = Pond.objects.create(
            owner=self.user,
            name='Health Pond',
            location='Natore',
            area_decimal=Decimal('20.00'),
            average_depth_ft=Decimal('5.00'),
            stocking_capacity=1000,
        )

    def test_disease_profile_requires_name_and_symptoms(self):
        disease = DiseaseProfile(name=' ', symptoms=[], description='Description')

        with self.assertRaises(ValidationError) as raised:
            disease.clean()

        self.assertEqual(set(raised.exception.message_dict), {'name'})

    def test_disease_profile_requires_at_least_one_symptom(self):
        disease = DiseaseProfile(name='Ich', symptoms=[], description='Description')

        with self.assertRaises(ValidationError) as raised:
            disease.clean()

        self.assertEqual(set(raised.exception.message_dict), {'symptoms'})

    def test_health_record_rejects_negative_counts(self):
        record = HealthRecord(
            pond=self.pond,
            created_by=self.user,
            observed_at=timezone.make_aware(datetime(2026, 8, 1)),
            affected_count=-1,
            mortality_count=0,
        )

        with self.assertRaises(ValidationError) as raised:
            record.clean()

        self.assertEqual(set(raised.exception.message_dict), {'affected_count'})

    def test_health_record_rejects_negative_mortality_count(self):
        record = HealthRecord(
            pond=self.pond,
            created_by=self.user,
            observed_at=timezone.make_aware(datetime(2026, 8, 1)),
            mortality_count=-1,
        )

        with self.assertRaises(ValidationError) as raised:
            record.clean()

        self.assertEqual(set(raised.exception.message_dict), {'mortality_count'})

    def test_treatment_plan_rejects_invalid_date_and_cost(self):
        treatment = TreatmentPlan(
            pond=self.pond,
            created_by=self.user,
            medicine_name='Salt bath',
            dosage='10 g/L',
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 1),
            cost=Decimal('0.00'),
        )

        with self.assertRaises(ValidationError) as raised:
            treatment.clean()

        self.assertEqual(set(raised.exception.message_dict), {'end_date'})

    def test_treatment_plan_rejects_negative_cost(self):
        treatment = TreatmentPlan(
            pond=self.pond,
            created_by=self.user,
            medicine_name='Salt bath',
            dosage='10 g/L',
            start_date=date(2026, 8, 1),
            cost=Decimal('-1.00'),
        )

        with self.assertRaises(ValidationError) as raised:
            treatment.clean()

        self.assertEqual(set(raised.exception.message_dict), {'cost'})

    def test_string_representations_are_descriptive(self):
        disease = DiseaseProfile(name='Ich', symptoms=['white spots'], description='Parasite')
        record = HealthRecord(
            pond=self.pond,
            created_by=self.user,
            observed_at=timezone.make_aware(datetime(2026, 8, 1)),
        )
        treatment = TreatmentPlan(
            pond=self.pond,
            created_by=self.user,
            medicine_name='Salt bath',
            dosage='10 g/L',
            start_date=date(2026, 8, 1),
        )

        self.assertEqual(str(disease), 'Ich')
        self.assertIn('Health Pond health record on 2026-08-01', str(record))
        self.assertEqual(str(treatment), 'Salt bath for Health Pond')
