from django.db import migrations, models


def forwards_convert_choice_values(apps, schema_editor):
    AssessmentSubmission = apps.get_model('tathmini', 'AssessmentSubmission')

    current_situation_map = {
        'madaftari': 'notebooks',
        'kompyuta': 'computer_systems',
        'mkabidhi': 'delegated_manager',
    }

    goals_map = {
        'kusimamia-mwenyewe': 'self_manage',
        'kukabidhi-mtu': 'delegate_with_visibility',
    }

    challenges_map = {
        'ugumu-rekodi': 'record_keeping',
        'wachelewa-kulipa': 'late_rent',
        'kukua-taratibu': 'slow_growth',
        'gharama-kubwa': 'high_maintenance_costs',
        'ukosefu-wakati': 'limited_time',
    }

    for submission in AssessmentSubmission.objects.all().iterator():
        updated_fields = []

        new_current = current_situation_map.get(submission.current_situation)
        if new_current and submission.current_situation != new_current:
            submission.current_situation = new_current
            updated_fields.append('current_situation')

        new_goal = goals_map.get(submission.goals)
        if new_goal and submission.goals != new_goal:
            submission.goals = new_goal
            updated_fields.append('goals')

        if submission.challenges:
            parts = [part.strip() for part in submission.challenges.split(',') if part.strip()]
            converted = [challenges_map.get(part, part) for part in parts]
            new_challenges = ','.join(converted)
            if new_challenges != submission.challenges:
                submission.challenges = new_challenges
                updated_fields.append('challenges')

        if updated_fields:
            submission.save(update_fields=updated_fields)


def backwards_convert_choice_values(apps, schema_editor):
    AssessmentSubmission = apps.get_model('tathmini', 'AssessmentSubmission')

    current_situation_map = {
        'notebooks': 'madaftari',
        'computer_systems': 'kompyuta',
        'delegated_manager': 'mkabidhi',
    }

    goals_map = {
        'self_manage': 'kusimamia-mwenyewe',
        'delegate_with_visibility': 'kukabidhi-mtu',
    }

    challenges_map = {
        'record_keeping': 'ugumu-rekodi',
        'late_rent': 'wachelewa-kulipa',
        'slow_growth': 'kukua-taratibu',
        'high_maintenance_costs': 'gharama-kubwa',
        'limited_time': 'ukosefu-wakati',
    }

    for submission in AssessmentSubmission.objects.all().iterator():
        updated_fields = []

        old_current = current_situation_map.get(submission.current_situation)
        if old_current and submission.current_situation != old_current:
            submission.current_situation = old_current
            updated_fields.append('current_situation')

        old_goal = goals_map.get(submission.goals)
        if old_goal and submission.goals != old_goal:
            submission.goals = old_goal
            updated_fields.append('goals')

        if submission.challenges:
            parts = [part.strip() for part in submission.challenges.split(',') if part.strip()]
            converted = [challenges_map.get(part, part) for part in parts]
            old_challenges = ','.join(converted)
            if old_challenges != submission.challenges:
                submission.challenges = old_challenges
                updated_fields.append('challenges')

        if updated_fields:
            submission.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('tathmini', '0003_subscriber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentsubmission',
            name='current_situation',
            field=models.CharField(
                choices=[
                    ('notebooks', 'I manage using notebooks'),
                    ('computer_systems', 'I manage using different computer systems'),
                    ('delegated_manager', 'I delegated someone to help me manage'),
                ],
                max_length=20,
                verbose_name='Current Situation',
            ),
        ),
        migrations.AlterField(
            model_name='assessmentsubmission',
            name='goals',
            field=models.CharField(
                choices=[
                    ('self_manage', 'Manage my properties myself with a good system'),
                    ('delegate_with_visibility', 'Delegate management while staying directly involved through a system'),
                ],
                max_length=50,
                verbose_name='Goals',
            ),
        ),
        migrations.RunPython(forwards_convert_choice_values, backwards_convert_choice_values),
    ]
