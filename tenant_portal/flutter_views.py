"""
Flutter / mobile API endpoints for the tenant_portal app.
Copied from api.py — web JS still uses api.py, Flutter URLs point here.
All views require tenant authentication (returns JSON 401/403 on failure).
"""
from datetime import date, timedelta
import calendar as cal

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from dashboardd.models import MaintenanceRequest, Payment
from .models import TenantNotification
from .views import _next_due_date, _get_tenant


def _tenant_api_guard(view_func):
    """Like tenant_required but returns JSON 401/403 instead of HTML."""
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
def api_tenant_profile(request):
    from .views import _eligibility
    tenant = _get_tenant(request.user)

    all_tenancies = list(request.user.tenant_profiles.select_related('property', 'unit', 'property__owner'))
    tenancies = []
    for t in all_tenancies:
        el = _eligibility(t)
        tenancies.append({
            'id': t.id,
            'property_name': t.property.name,
            'property_address': t.property.address,
            'unit': t.unit.unit_number if t.unit else None,
            'landlord': t.property.owner.get_full_name() or t.property.owner.username if t.property.owner else None,
            'status': t.status,
            'status_label': t.get_status_display(),
            'move_in_date': t.move_in_date.strftime('%d %b %Y') if t.move_in_date else None,
            'eligible_until': el['eligible_until'].strftime('%d %b %Y') if (el and el['eligible_until']) else None,
            'eligible_until_raw': str(el['eligible_until']) if (el and el['eligible_until']) else None,
            'days_left': el['days_left'] if el else None,
            'months_paid': el['months_paid'] if el else 0,
            'notifications_enabled': t.notifications_enabled,
            'is_primary': t.pk == tenant.pk,
        })

    return JsonResponse({
        'name': f"{tenant.first_name} {tenant.last_name}",
        'first_name': tenant.first_name,
        'last_name': tenant.last_name,
        'email': tenant.email or '',
        'phone': tenant.phone or '',
        'status': tenant.status,
        'status_label': tenant.get_status_display(),
        'profile_picture': tenant.profile_picture.url if tenant.profile_picture else None,
        'tenancies': tenancies,
    })


@_tenant_api_guard
@csrf_exempt
@require_POST
def api_tenant_update_profile(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    tenant = _get_tenant(request.user)
    allowed = ['first_name', 'last_name', 'email', 'phone', 'emergency_contact', 'emergency_phone']
    for field in allowed:
        if field in data:
            setattr(tenant, field, data[field].strip())
    tenant.save(update_fields=[f for f in allowed if f in data])

    # Mirror name to the auth user
    if 'first_name' in data:
        request.user.first_name = data['first_name'].strip()
    if 'last_name' in data:
        request.user.last_name = data['last_name'].strip()
    if 'first_name' in data or 'last_name' in data:
        request.user.save(update_fields=['first_name', 'last_name'])

    return JsonResponse({'success': True})


@_tenant_api_guard
@require_GET
def api_tenant_maintenance(request):
    tenant = _get_tenant(request.user)
    qs = MaintenanceRequest.objects.filter(tenant=tenant).order_by('-reported_date')
    items = [
        {
            'id': r.id,
            'title': r.title,
            'description': r.description,
            'priority': r.priority,
            'priority_label': r.get_priority_display(),
            'status': r.status,
            'status_label': r.get_status_display(),
            'reported_date': r.reported_date.strftime('%d %b %Y'),
            'completed_date': r.completed_date.strftime('%d %b %Y') if r.completed_date else None,
        }
        for r in qs
    ]
    return JsonResponse({'requests': items})


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
