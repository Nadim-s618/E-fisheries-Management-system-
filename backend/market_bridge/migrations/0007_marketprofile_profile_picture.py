from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('market_bridge', '0006_marketorder_transaction_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketprofile',
            name='profile_picture',
            field=models.FileField(blank=True, null=True, upload_to='profile_pictures/'),
        ),
    ]
