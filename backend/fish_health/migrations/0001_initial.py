import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

from fish_health.services.core.disease_library import DEFAULT_DISEASES


def seed_disease_profiles(apps, schema_editor):
    DiseaseProfile = apps.get_model('fish_health', 'DiseaseProfile')

    for disease in DEFAULT_DISEASES:
        DiseaseProfile.objects.update_or_create(
            name=disease['name'],
            defaults=disease,
        )


def unseed_disease_profiles(apps, schema_editor):
    DiseaseProfile = apps.get_model('fish_health', 'DiseaseProfile')
    DiseaseProfile.objects.filter(
        name__in=[disease['name'] for disease in DEFAULT_DISEASES],
    ).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0003_notification'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiseaseProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, unique=True)),
                ('species', models.JSONField(blank=True, default=list)),
                ('symptoms', models.JSONField(default=list)),
                ('description', models.TextField()),
                ('risk_level', models.CharField(choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High'), ('Critical', 'Critical')], default='Moderate', max_length=16)),
                ('recommended_treatments', models.JSONField(blank=True, default=list)),
                ('prevention', models.JSONField(blank=True, default=list)),
                ('environmental_triggers', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='HealthRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('observed_at', models.DateTimeField()),
                ('species', models.CharField(blank=True, max_length=120)),
                ('symptoms', models.JSONField(blank=True, default=list)),
                ('symptom_notes', models.TextField(blank=True)),
                ('abnormal_behavior', models.TextField(blank=True)),
                ('affected_count', models.PositiveIntegerField(default=0)),
                ('mortality_count', models.PositiveIntegerField(default=0)),
                ('severity', models.CharField(choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High'), ('Critical', 'Critical')], default='Moderate', max_length=16)),
                ('status', models.CharField(choices=[('Open', 'Open'), ('Monitoring', 'Monitoring'), ('Treatment', 'Treatment'), ('Resolved', 'Resolved')], default='Open', max_length=16)),
                ('water_quality_snapshot', models.JSONField(blank=True, default=dict)),
                ('weather_snapshot', models.JSONField(blank=True, default=dict)),
                ('possible_diseases', models.JSONField(blank=True, default=list)),
                ('ai_recommendation', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fish_health_records', to=settings.AUTH_USER_MODEL)),
                ('fish_stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='health_records', to='store.fishstock')),
                ('pond', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='health_records', to='store.pond')),
            ],
            options={
                'ordering': ['-observed_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TreatmentPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medicine_name', models.CharField(max_length=160)),
                ('dosage', models.CharField(max_length=160)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('instructions', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('Planned', 'Planned'), ('Active', 'Active'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Planned', max_length=16)),
                ('outcome_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fish_treatment_plans', to=settings.AUTH_USER_MODEL)),
                ('disease', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='treatment_plans', to='fish_health.diseaseprofile')),
                ('fish_stock', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='treatment_plans', to='store.fishstock')),
                ('health_record', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='treatment_plans', to='fish_health.healthrecord')),
                ('pond', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='treatment_plans', to='store.pond')),
            ],
            options={
                'ordering': ['-start_date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='healthrecord',
            index=models.Index(fields=['pond', '-observed_at'], name='fish_health_pond_id_cfc5d4_idx'),
        ),
        migrations.AddIndex(
            model_name='healthrecord',
            index=models.Index(fields=['status', 'severity'], name='fish_health_status_cbb4f0_idx'),
        ),
        migrations.AddIndex(
            model_name='treatmentplan',
            index=models.Index(fields=['pond', 'status'], name='fish_health_pond_id_a1b210_idx'),
        ),
        migrations.RunPython(seed_disease_profiles, reverse_code=unseed_disease_profiles),
    ]
