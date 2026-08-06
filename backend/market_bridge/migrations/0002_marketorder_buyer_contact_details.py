# Generated for mandatory buyer contact details on market orders.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market_bridge', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketorder',
            name='buyer_address',
            field=models.CharField(default='', max_length=260),
        ),
        migrations.AddField(
            model_name='marketorder',
            name='buyer_contact_number',
            field=models.CharField(default='', max_length=40),
        ),
        migrations.AddField(
            model_name='marketorder',
            name='buyer_full_name',
            field=models.CharField(default='', max_length=140),
        ),
    ]
