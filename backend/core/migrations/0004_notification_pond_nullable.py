import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='pond',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name='notifications',
                to='store.pond',
            ),
        ),
    ]
