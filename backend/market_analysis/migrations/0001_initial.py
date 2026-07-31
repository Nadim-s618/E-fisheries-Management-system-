# Generated manually for the market analysis app.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='MarketPriceSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fish_name', models.CharField(max_length=80)),
                ('division', models.CharField(max_length=80)),
                ('recorded_date', models.DateField()),
                ('price_per_kg', models.DecimalField(decimal_places=2, max_digits=8)),
                ('demand_level', models.CharField(choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], default='Medium', max_length=12)),
                ('source', models.CharField(default='Generated sample', max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-recorded_date', 'division', 'fish_name'],
            },
        ),
        migrations.AddIndex(
            model_name='marketpricesnapshot',
            index=models.Index(fields=['division', 'fish_name', '-recorded_date'], name='market_anal_divisio_64aef4_idx'),
        ),
        migrations.AddIndex(
            model_name='marketpricesnapshot',
            index=models.Index(fields=['recorded_date'], name='market_anal_recorde_33a0ab_idx'),
        ),
        migrations.AddConstraint(
            model_name='marketpricesnapshot',
            constraint=models.UniqueConstraint(fields=('fish_name', 'division', 'recorded_date'), name='unique_market_price_snapshot'),
        ),
    ]
