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
    message = f"Msimbo wako wa uthibitisho ni: {code}\nHalali kwa dakika 10. Usishirikishe mtu yeyote."
    return send_sms(phone, message)


def send_payment_reminder(tenant, payment) -> bool:
    """Remind a tenant about a pending/overdue payment."""
    from django.utils import timezone
    today = timezone.now().date()
    days_overdue = (today - payment.due_date).days if payment.due_date < today else 0

    if days_overdue > 0:
        message = (
            f"Habari {tenant.first_name},\n"
            f"Kodi yako ya TZS {payment.amount:,.0f} imechelewa siku {days_overdue}. "
            f"Tafadhali lipa haraka iwezekanavyo.\n"
            f"- Maghettoni"
        )
    else:
        message = (
            f"Habari {tenant.first_name},\n"
            f"Kodi yako ya TZS {payment.amount:,.0f} inakaribia kulipwa tarehe {payment.due_date.strftime('%d/%m/%Y')}. "
            f"Tafadhali hakikisha umelipa kwa wakati.\n"
            f"- Maghettoni"
        )
    return send_sms(tenant.phone, message)


def send_maintenance_update(tenant, req) -> bool:
    """Notify a tenant about their maintenance request status."""
    status_labels = {
        'pending': 'inasubiri',
        'in_progress': 'inashughulikiwa',
        'completed': 'imekamilika',
        'cancelled': 'imefutwa',
    }
    status_text = status_labels.get(req.status, req.status)
    message = (
        f"Habari {tenant.first_name},\n"
        f"Ombi lako la matengenezo '{req.title}' sasa liko: {status_text}.\n"
        f"Mali: {req.property.name}, Chumba: {req.unit.unit_number}.\n"
        f"- Maghettoni"
    )
    return send_sms(tenant.phone, message)

