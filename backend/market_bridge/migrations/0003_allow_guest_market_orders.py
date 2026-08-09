import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('market_bridge', '0002_marketorder_buyer_contact_details'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketorder',
            name='buyer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='market_orders',
                to='auth.user',
            ),
        ),
    ]
