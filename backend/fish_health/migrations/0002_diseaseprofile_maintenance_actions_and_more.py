from django.db import migrations, models

from fish_health.services.core.disease_library import DISEASE_TREATMENT_GUIDES


def seed_treatment_guides(apps, schema_editor):
    DiseaseProfile = apps.get_model('fish_health', 'DiseaseProfile')

    for disease_name, guide in DISEASE_TREATMENT_GUIDES.items():
        DiseaseProfile.objects.filter(name=disease_name).update(
            treatment_protocols=guide['treatment_protocols'],
            maintenance_actions=guide['maintenance_actions'],
        )


def clear_treatment_guides(apps, schema_editor):
    DiseaseProfile = apps.get_model('fish_health', 'DiseaseProfile')
    DiseaseProfile.objects.filter(
        name__in=DISEASE_TREATMENT_GUIDES.keys(),
    ).update(
        treatment_protocols=[],
        maintenance_actions=[],
    )


class Migration(migrations.Migration):

    dependencies = [
        ('fish_health', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='diseaseprofile',
            name='maintenance_actions',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='diseaseprofile',
            name='treatment_protocols',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(seed_treatment_guides, reverse_code=clear_treatment_guides),
    ]
