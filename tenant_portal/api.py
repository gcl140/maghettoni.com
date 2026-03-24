from datetime import date, timedelta
import calendar as cal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from dashboardd.models import MaintenanceRequest, Payment
from .models import TenantNotification
from .views import _next_due_date, tenant_required, _get_tenant


def _tenant_api_guard(view_func):
    """Like tenant_required but returns JSON 403 instead of HTML."""
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthenticated'}, status=401)
        if not request.user.tenant_profiles.exists():
            return JsonResponse({'error': 'No tenant profile linked'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


@_tenant_api_guard
@require_GET
def api_tenant_dashboard(request):
    tenant = _get_tenant(request.user)
    today = date.today()
    next_due = _next_due_date(tenant)

    recent_qs = Payment.objects.filter(tenant=tenant).order_by('-payment_date')
    try:
        limit = int(request.GET['limit'])
        recent_qs = recent_qs[:limit]
    except (KeyError, ValueError, TypeError):
        recent_qs = recent_qs[:5]  # default 5 for dashboard
    recent_payments = list(recent_qs.values(
        'id', 'amount', 'payment_date', 'status', 'reference_number'
    ))
    for p in recent_payments:
        p['amount'] = float(p['amount'])
        p['payment_date'] = str(p['payment_date'])

    overdue = Payment.objects.filter(
        tenant=tenant, due_date__lt=today, status__in=['pending', 'failed']
    ).count()

    pending_maint = MaintenanceRequest.objects.filter(
        tenant=tenant, status__in=['pending', 'in_progress']
    ).count()

    monthly_rent = float(tenant.unit.monthly_rent) if tenant.unit else 0

    # Calculated eligible_until (no stored move_out_date anymore)
    from .views import _eligibility
    el = _eligibility(tenant)
    eligible_until = str(el['eligible_until']) if (el and el['eligible_until']) else None

    return JsonResponse({
        'monthly_rent': monthly_rent,
        'next_due': str(next_due),
        'days_until_due': (next_due - today).days,
        'overdue_count': overdue,
        'pending_maintenance': pending_maint,
        'recent_payments': recent_payments,
        'stay_start': str(tenant.move_in_date),
        'eligible_until': eligible_until,
    })


@_tenant_api_guard
@require_GET
def api_tenant_calendar(request):
    """Return payment events for a given year/month."""
    tenant = _get_tenant(request.user)
    today = date.today()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if not (1 <= month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid year/month'}, status=400)

    due_day = tenant.move_in_date.day
    last_day = cal.monthrange(year, month)[1]
    actual_due_day = min(due_day, last_day)

    made = list(
        Payment.objects.filter(
            tenant=tenant,
            payment_date__year=year,
            payment_date__month=month,
        ).values('payment_date', 'status', 'amount')
    )
    made_out = [
        {'day': p['payment_date'].day, 'status': p['status'], 'amount': float(p['amount'])}
        for p in made
    ]

    from .views import _eligibility
    elig = _eligibility(tenant)
    eligible_until = elig['eligible_until'] if elig else None
    eligible_until_day = (
        eligible_until.day
        if eligible_until and eligible_until.year == year and eligible_until.month == month
        else None
    )

    return JsonResponse({
        'year': year,
        'month': month,
        'days_in_month': last_day,
        'due_day': actual_due_day,
        'payments_made': made_out,
        'today': today.day if (today.year == year and today.month == month) else None,
        'eligible_until_day': eligible_until_day,
    })


@_tenant_api_guard
@require_GET
def api_tenant_payments(request):
    tenant = _get_tenant(request.user)
    qs = Payment.objects.filter(tenant=tenant).order_by('-payment_date')
    try:
        limit = int(request.GET['limit'])
        qs = qs[:limit]
    except (KeyError, ValueError, TypeError):
        pass  # no limit — fetch all
    payments = list(qs.values(
        'id', 'amount', 'payment_date', 'due_date',
        'payment_method', 'status', 'reference_number',
    ))
    for p in payments:
        p['amount'] = float(p['amount'])
        p['payment_date'] = str(p['payment_date'])
        p['due_date'] = str(p['due_date'])
    return JsonResponse({'payments': payments})


@_tenant_api_guard
@require_GET
def api_tenant_notifications(request):
    tenant = _get_tenant(request.user)

    unread_qs = TenantNotification.objects.filter(tenant=tenant, is_read=False)
    unread_qs.update(is_read=True)

    notifs = TenantNotification.objects.filter(tenant=tenant).order_by('-created_at')[:20]
    items = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'unread': not n.is_read,
            'created_at': n.created_at.strftime('%d %b %Y, %H:%M'),
        }
        for n in notifs
    ]
    return JsonResponse({'items': items, 'unread_count': 0})
