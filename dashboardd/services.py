import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

BEEM_URL = "https://apisms.beem.africa/v1/send"


def send_sms(phone: str, message: str) -> bool:
    """
    Send an SMS via Beem Africa.
    phone should be in international format, e.g. '255758523353'
    Returns True on success, False on failure.
    """
    if not settings.BEEM_API_KEY or not settings.BEEM_SECRET_KEY:
        logger.error("Beem credentials not configured (BEEM_API_KEY / BEEM_SECRET_KEY missing)")
        return False

    # Normalise phone: strip leading + or 0, ensure 255 prefix
    phone = phone.strip().lstrip('+')
    if phone.startswith('0'):
        phone = '255' + phone[1:]

    payload = {
        "source_addr": settings.BEEM_SENDER_ID,
        "encoding": 0,
        "message": message,
        "recipients": [
            {"recipient_id": 1, "dest_addr": phone}
        ],
    }

    try:
        response = requests.post(
            BEEM_URL,
            json=payload,
            auth=HTTPBasicAuth(settings.BEEM_API_KEY, settings.BEEM_SECRET_KEY),
            timeout=10,
        )
        if response.status_code == 200:
            logger.info(f"SMS sent to {phone}")
            return True
        else:
            logger.error(f"Beem SMS failed for {phone}: {response.status_code} {response.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"Beem SMS request error for {phone}: {e}")
        return False


def send_otp(phone: str, code: str) -> bool:
    message = f"Your verification code is: {code}\nValid for 10 minutes. Do not share with anyone."
    return send_sms(phone, message)


def send_payment_reminder(tenant, payment) -> bool:
    """Remind a tenant about a pending/overdue payment."""
    from django.utils import timezone
    today = timezone.now().date()
    days_overdue = (today - payment.due_date).days if payment.due_date < today else 0

    if days_overdue > 0:
        message = (
            f"Hello {tenant.first_name},\n"
            f"Your rent of TZS {payment.amount:,.0f} is {days_overdue} day(s) overdue. "
            f"Please pay as soon as possible.\n"
            f"- Maghettoni"
        )
    else:
        message = (
            f"Hello {tenant.first_name},\n"
            f"Your rent of TZS {payment.amount:,.0f} is due on {payment.due_date.strftime('%d/%m/%Y')}. "
            f"Please ensure payment is made on time.\n"
            f"- Maghettoni"
        )
    return send_sms(tenant.phone, message)


def send_payment_reminder_email(tenant, payment) -> bool:
    """Send a payment reminder email to the tenant."""
    from django.core.mail import send_mail
    from django.utils import timezone
    if not tenant.email:
        return False
    today = timezone.now().date()
    days_overdue = (today - payment.due_date).days if payment.due_date and payment.due_date < today else 0
    if days_overdue > 0:
        subject = f"Overdue Payment Reminder — TZS {payment.amount:,.0f}"
        body = (
            f"Dear {tenant.first_name},\n\n"
            f"Your rent payment of TZS {payment.amount:,.0f} for {payment.property.name} "
            f"is {days_overdue} day(s) overdue (was due {payment.due_date.strftime('%d %b %Y')}).\n\n"
            f"Reference: {payment.reference_number or 'N/A'}\n\n"
            f"Please settle this as soon as possible.\n\n"
            f"— Maghettoni"
        )
    else:
        subject = f"Payment Reminder — TZS {payment.amount:,.0f} due {payment.due_date.strftime('%d %b %Y')}"
        body = (
            f"Dear {tenant.first_name},\n\n"
            f"This is a reminder that your rent payment of TZS {payment.amount:,.0f} "
            f"for {payment.property.name} is due on {payment.due_date.strftime('%d %b %Y')}.\n\n"
            f"Reference: {payment.reference_number or 'N/A'}\n\n"
            f"Please ensure payment is made on time.\n\n"
            f"— Maghettoni"
        )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [tenant.email], fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Payment reminder email failed for tenant {tenant.id}: {e}")
        return False


def send_eligibility_reminder_sms(tenant, eligible_until, days_left: int, reminder_type: str) -> bool:
    """SMS reminder about eligibility / expected move-out date."""
    if not tenant.phone:
        return False
    if reminder_type == 'halfway':
        msg = (
            f"Habari {tenant.first_name},\n"
            f"Uko nusu njia ya muda wako wa kukaa kwenye {tenant.property.name}. "
            f"Muda wako unaisha {eligible_until.strftime('%d %b %Y')}. "
            f"Hakikisha malipo yako yanafanywa kwa wakati.\n- Maghettoni"
        )
    elif reminder_type == 'one_month':
        msg = (
            f"Habari {tenant.first_name},\n"
            f"Mwezi 1 umebaki kukaa kwenye {tenant.property.name} (Unit {tenant.unit.unit_number if tenant.unit else ''}). "
            f"Muda wako unaisha {eligible_until.strftime('%d %b %Y')}. "
            f"Lipa au wasiliana na landlord wako.\n- Maghettoni"
        )
    elif reminder_type == 'two_weeks':
        msg = (
            f"Habari {tenant.first_name},\n"
            f"Siku 14 zimebaki! Muda wako kwenye {tenant.property.name} unaisha {eligible_until.strftime('%d %b %Y')}. "
            f"Hatua ya haraka inahitajika.\n- Maghettoni"
        )
    else:  # daily
        msg = (
            f"Habari {tenant.first_name},\n"
            f"Siku {days_left} zimebaki kwenye {tenant.property.name}. "
            f"Muda wako unaisha {eligible_until.strftime('%d %b %Y')}.\n- Maghettoni"
        )
    return send_sms(tenant.phone, msg)


def send_eligibility_reminder_email(tenant, eligible_until, days_left: int, reminder_type: str) -> bool:
    """Email reminder about eligibility / expected move-out date."""
    from django.core.mail import send_mail
    if not tenant.email:
        return False
    unit_str = f"Unit {tenant.unit.unit_number}" if tenant.unit else ""
    subject_map = {
        'halfway': f"Halfway through your stay at {tenant.property.name}",
        'one_month': f"1 month left at {tenant.property.name} — action needed",
        'two_weeks': f"2 weeks left at {tenant.property.name}",
        'daily': f"{days_left} day{'s' if days_left != 1 else ''} left at {tenant.property.name}",
    }
    subject = subject_map.get(reminder_type, f"Stay reminder — {tenant.property.name}")
    body = (
        f"Dear {tenant.first_name},\n\n"
        f"This is a reminder about your tenancy at {tenant.property.name}"
        f"{' — ' + unit_str if unit_str else ''}.\n\n"
        f"Based on your completed payments, your eligibility expires on "
        f"{eligible_until.strftime('%d %B %Y')} ({days_left} day{'s' if days_left != 1 else ''} remaining).\n\n"
        f"If you plan to continue, please make a new payment to extend your stay. "
        f"If you are leaving, you can disable these reminders from your tenant portal profile.\n\n"
        f"— Maghettoni\n"
        f"  {tenant.property.name}"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [tenant.email], fail_silently=False)
        return True
    except Exception as e:
        logger.error(f"Eligibility reminder email failed for tenant {tenant.id}: {e}")
        return False


def send_maintenance_update(tenant, req) -> bool:
    """Notify a tenant about their maintenance request status."""
    status_labels = {
        'pending': 'pending',
        'in_progress': 'in progress',
        'completed': 'completed',
        'cancelled': 'cancelled',
    }
    status_text = status_labels.get(req.status, req.status)
    message = (
        f"Hello {tenant.first_name},\n"
        f"Your maintenance request '{req.title}' is now: {status_text}.\n"
        f"Property: {req.property.name}, Unit: {req.unit.unit_number}.\n"
        f"- Maghettoni"
    )
    return send_sms(tenant.phone, message)

