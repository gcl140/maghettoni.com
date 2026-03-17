from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboardd', '0015_unit_amenities'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='landlord_confirmed',
            field=models.BooleanField(
                default=False,
                help_text='Landlord has confirmed physical receipt of this payment.',
            ),
        ),
    ]
