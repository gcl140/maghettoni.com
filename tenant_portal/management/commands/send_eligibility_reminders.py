from django.core.management.base import BaseCommand
from tenant_portal.tasks import send_eligibility_reminders


class Command(BaseCommand):
    help = 'Send eligibility/move-out reminders to tenants whose stay is ending soon.'

    def handle(self, *args, **options):
        count = send_eligibility_reminders()
        self.stdout.write(self.style.SUCCESS(f'Done — {count} reminder(s) sent.'))
