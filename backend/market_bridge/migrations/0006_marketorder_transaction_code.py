from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('market_bridge', '0005_marketorder_delivery_statuses'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketorder',
            name='transaction_code',
            field=models.CharField(blank=True, db_index=True, default='', max_length=20),
        ),
    ]
