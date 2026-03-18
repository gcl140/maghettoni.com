"""
Celery tasks for tenant eligibility reminders.

Reminder schedule per tenancy:
- halfway   : when days_remaining <= total_days / 2 (only once)
- one_month : when days_remaining <= 30
- two_weeks : when days_remaining <= 14
- daily     : every day when days_remaining <= 7

All reminders respect tenant.notifications_enabled and are deduped via
EligibilityReminder (one row per tenant + type + eligible_until cycle).

Run the beat scheduler alongside the worker:
  celery -A maghettoni beat -l info
  celery -A maghettoni worker -l info
"""

import calendar as _cal
import logging
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)


def _calc_eligibility(tenant):
    """Return (months_paid, eligible_until, days_left) or None."""
    if not tenant.unit or not tenant.unit.monthly_rent:
        return None
    from django.db.models import Sum
    monthly_rent = tenant.unit.monthly_rent
    total_paid = (
        tenant.payments.filter(status='completed')
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    months_paid = int(total_paid / monthly_rent)
    if months_paid <= 0:
        return None

    start = tenant.move_in_date
    m = start.month + months_paid - 1
    year = start.year + m // 12
    month = m % 12 + 1
    last_day = _cal.monthrange(year, month)[1]
    eligible_until = date(year, month, min(start.day, last_day))

    today = date.today()
    if eligible_until < today:
        return None  # Already expired — no point reminding

    days_left = (eligible_until - today).days
    total_days = (eligible_until - start).days
    return months_paid, eligible_until, days_left, total_days


@shared_task(name='tenant_portal.tasks.send_eligibility_reminders')
def send_eligibility_reminders():
    """
    Daily task: check every active tenant with notifications enabled
    and send appropriate reminders.
    """
    from dashboardd.models import Tenant
    from dashboardd.services import send_eligibility_reminder_sms, send_eligibility_reminder_email
    from .models import EligibilityReminder

    tenants = Tenant.objects.filter(
        status='active',
        notifications_enabled=True,
        unit__isnull=False,
    ).select_related('unit', 'property')

    sent_count = 0

    for tenant in tenants:
        result = _calc_eligibility(tenant)
        if not result:
            continue
        months_paid, eligible_until, days_left, total_days = result

        # Determine which reminder types fire today
        triggers = []
        if days_left <= 7:
            triggers.append('daily')
        if days_left <= 14:
            triggers.append('two_weeks')
        if days_left <= 30:
            triggers.append('one_month')
        if total_days > 0 and days_left <= total_days // 2:
            triggers.append('halfway')

        for rtype in triggers:
            # 'daily' is allowed once per day per cycle; others only once per cycle
            already_sent = EligibilityReminder.objects.filter(
                tenant=tenant,
                reminder_type=rtype,
                eligible_until=eligible_until,
            ).exists()

            # For daily reminders, check if sent today specifically
            if rtype == 'daily' and already_sent:
                sent_today = EligibilityReminder.objects.filter(
                    tenant=tenant,
                    reminder_type='daily',
                    eligible_until=eligible_until,
                    sent_at__date=date.today(),
                ).exists()
                if sent_today:
                    continue
            elif already_sent:
                continue

            # Send SMS + email
            sms_ok = send_eligibility_reminder_sms(tenant, eligible_until, days_left, rtype)
            email_ok = send_eligibility_reminder_email(tenant, eligible_until, days_left, rtype)

            if sms_ok or email_ok:
                EligibilityReminder.objects.get_or_create(
                    tenant=tenant,
                    reminder_type=rtype,
                    eligible_until=eligible_until,
                )
                sent_count += 1
                logger.info(
                    f"Sent '{rtype}' reminder to tenant {tenant.id} "
                    f"({tenant.first_name} {tenant.last_name}) — {days_left}d left"
                )

    logger.info(f"send_eligibility_reminders: {sent_count} reminder(s) sent across {tenants.count()} tenants")
    return sent_count
