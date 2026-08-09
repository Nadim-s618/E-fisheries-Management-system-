from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('market_bridge', '0003_allow_guest_market_orders'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketlisting',
            name='average_height_cm',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='marketlisting',
            name='average_weight_g',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
