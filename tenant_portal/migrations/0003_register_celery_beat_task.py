from django.db import migrations


def create_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period='days',
    )
    PeriodicTask.objects.get_or_create(
        name='Daily eligibility reminders',
        defaults={
            'interval': schedule,
            'task': 'tenant_portal.tasks.send_eligibility_reminders',
            'enabled': True,
        },
    )


def remove_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(name='Daily eligibility reminders').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tenant_portal', '0002_add_eligibility_reminder'),
        ('django_celery_beat', '0019_alter_periodictasks_options'),
    ]

    operations = [
        migrations.RunPython(create_periodic_task, remove_periodic_task),
    ]
