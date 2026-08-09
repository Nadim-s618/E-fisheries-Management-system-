from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('market_bridge', '0004_marketlisting_average_measurements'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketorder',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('accepted', 'Accepted'),
                    ('shipped', 'Shipped'),
                    ('out_for_delivery', 'Out for delivery'),
                    ('rejected', 'Rejected'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='pending',
                max_length=16,
            ),
        ),
    ]
