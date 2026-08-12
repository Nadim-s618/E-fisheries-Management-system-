from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('financials', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financialtransaction',
            name='source_type',
            field=models.CharField(
                choices=[
                    ('manual', 'Manual'),
                    ('feed_purchase', 'Feed purchase'),
                    ('meal_feed', 'Meal feed'),
                    ('fish_stocking', 'Fish stocking'),
                    ('medicine_treatment', 'Medicine or treatment'),
                    ('labor', 'Labor'),
                    ('harvest_sale', 'Harvest sale'),
                    ('pond_maintenance', 'Pond maintenance'),
                    ('equipment_purchase', 'Equipment purchase'),
                ],
                default='manual',
                max_length=32,
            ),
        ),
    ]
