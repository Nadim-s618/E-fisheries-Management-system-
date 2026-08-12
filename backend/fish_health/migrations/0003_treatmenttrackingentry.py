from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('fish_health', '0002_diseaseprofile_maintenance_actions_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TreatmentTrackingEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Planned', 'Planned'), ('Active', 'Active'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=16)),
                ('administered_dosage', models.CharField(blank=True, max_length=160)),
                ('quantity_used', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('notes', models.TextField(blank=True)),
                ('follow_up_date', models.DateField(blank=True, null=True)),
                ('follow_up_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recorded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='treatment_tracking_entries', to=settings.AUTH_USER_MODEL)),
                ('treatment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracking_entries', to='fish_health.treatmentplan')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['treatment', '-created_at'], name='fish_health_treatme_3f44ae_idx')],
            },
        ),
    ]
