# Generated for fish feeding recommendations and tracking.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('store', '0003_notification'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedingRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recommendation_date', models.DateField()),
                ('recommended_feed_kg', models.DecimalField(decimal_places=2, max_digits=9)),
                ('feed_type', models.CharField(default='Floating Feed 32%', max_length=120)),
                ('price_per_kg', models.DecimalField(decimal_places=2, default=4.5, max_digits=8)),
                ('estimated_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('meals', models.PositiveSmallIntegerField(default=2)),
                ('schedule', models.JSONField(default=list)),
                ('reasons', models.JSONField(default=list)),
                ('input_summary', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('accepted', 'Accepted'), ('edited', 'Edited'), ('completed', 'Completed'), ('superseded', 'Superseded')], default='draft', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pond', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feeding_recommendations', to='store.pond')),
            ],
            options={
                'ordering': ['-recommendation_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FeedingSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meal_number', models.PositiveSmallIntegerField()),
                ('scheduled_at', models.DateTimeField()),
                ('planned_feed_kg', models.DecimalField(decimal_places=2, max_digits=9)),
                ('actual_feed_kg', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('skipped', 'Skipped')], default='pending', max_length=16)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pond', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feeding_sessions', to='store.pond')),
                ('recommendation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='feeding.feedingrecommendation')),
            ],
            options={
                'ordering': ['scheduled_at', 'meal_number'],
            },
        ),
        migrations.AddIndex(
            model_name='feedingrecommendation',
            index=models.Index(fields=['pond', 'recommendation_date', 'status'], name='feeding_fee_pond_id_374dcf_idx'),
        ),
        migrations.AddConstraint(
            model_name='feedingrecommendation',
            constraint=models.CheckConstraint(condition=models.Q(('recommended_feed_kg__gt', 0)), name='feeding_recommendation_feed_positive'),
        ),
        migrations.AddConstraint(
            model_name='feedingrecommendation',
            constraint=models.CheckConstraint(condition=models.Q(('price_per_kg__gte', 0)), name='feeding_recommendation_price_not_negative'),
        ),
        migrations.AddConstraint(
            model_name='feedingrecommendation',
            constraint=models.CheckConstraint(condition=models.Q(('estimated_cost__gte', 0)), name='feeding_recommendation_cost_not_negative'),
        ),
        migrations.AddConstraint(
            model_name='feedingrecommendation',
            constraint=models.CheckConstraint(condition=models.Q(('meals__gt', 0)), name='feeding_recommendation_meals_positive'),
        ),
        migrations.AddConstraint(
            model_name='feedingsession',
            constraint=models.UniqueConstraint(fields=('recommendation', 'meal_number'), name='unique_feeding_session_meal_per_recommendation'),
        ),
        migrations.AddConstraint(
            model_name='feedingsession',
            constraint=models.CheckConstraint(condition=models.Q(('meal_number__gt', 0)), name='feeding_session_meal_number_positive'),
        ),
        migrations.AddConstraint(
            model_name='feedingsession',
            constraint=models.CheckConstraint(condition=models.Q(('planned_feed_kg__gt', 0)), name='feeding_session_planned_feed_positive'),
        ),
        migrations.AddConstraint(
            model_name='feedingsession',
            constraint=models.CheckConstraint(condition=models.Q(('actual_feed_kg__isnull', True), ('actual_feed_kg__gt', 0), _connector='OR'), name='feeding_session_actual_feed_positive_when_set'),
        ),
    ]
