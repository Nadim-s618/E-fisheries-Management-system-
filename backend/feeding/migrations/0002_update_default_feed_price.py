from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('feeding', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedingrecommendation',
            name='price_per_kg',
            field=models.DecimalField(decimal_places=2, default=135.0, max_digits=8),
        ),
    ]
