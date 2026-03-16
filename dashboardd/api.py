from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Property, Unit, Tenant, Payment, MaintenanceRequest
from .services import send_payment_reminder, send_maintenance_update


# ── Helpers ──────────────────────────────────────────────────────────────────

def _paginate(qs, request, per_page=20):
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    total = qs.count()
    start = (page - 1) * per_page
    items = list(qs[start:start + per_page])
    return items, {'page': page, 'per_page': per_page, 'total': total, 'pages': -(-total // per_page)}


# ── Properties ────────────────────────────────────────────────────────────────

@login_required
@require_GET
def api_properties(request):
    qs = Property.objects.filter(owner=request.user)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(address__icontains=search)

    ptype = request.GET.get('type')
    if ptype:
        qs = qs.filter(property_type=ptype)

    items, meta = _paginate(qs, request)
    return JsonResponse({
        'results': [_serialize_property(p) for p in items],
        'meta': meta,
    })


@login_required
@require_GET
def api_property_detail(request, property_id):
    p = get_object_or_404(Property, id=property_id, owner=request.user)
    data = _serialize_property(p)
    data['units'] = [_serialize_unit(u) for u in p.units_list.all()]
    return JsonResponse(data)


def _serialize_property(p):
    return {
        'id': p.id,
        'name': p.name,
        'address': p.address,
        'type': p.property_type,
        'type_label': p.get_property_type_display(),
        'units': p.units,
        'image': p.image.url if p.image else None,
        'created_at': p.created_at.isoformat(),
    }


def _serialize_unit(u):
    return {
        'id': u.id,
        'unit_number': u.unit_number,
        'bedrooms': u.bedrooms,
        'bathrooms': u.bathrooms,
        'monthly_rent': float(u.monthly_rent),
        'is_occupied': u.is_occupied,
    }


# ── Tenants ───────────────────────────────────────────────────────────────────

@login_required
@require_GET
def api_tenants(request):
    qs = Tenant.objects.filter(property__owner=request.user)

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(first_name__icontains=search) \
             | qs.filter(last_name__icontains=search) \
             | qs.filter(phone__icontains=search) \
             | qs.filter(email__icontains=search)

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    property_id = request.GET.get('property_id')
    if property_id:
        qs = qs.filter(property_id=property_id)

    items, meta = _paginate(qs, request)
    return JsonResponse({
        'results': [_serialize_tenant(t) for t in items],
        'meta': meta,
    })


@login_required
@require_GET
def api_tenant_detail(request, tenant_id):
    t = get_object_or_404(Tenant, id=tenant_id, property__owner=request.user)
    return JsonResponse(_serialize_tenant(t, full=True))


def _serialize_tenant(t, full=False):
    data = {
        'id': t.id,
        'full_name': f"{t.first_name} {t.last_name}",
        'first_name': t.first_name,
        'last_name': t.last_name,
        'email': t.email,
        'phone': t.phone,
        'status': t.status,
        'status_label': t.get_status_display(),
        'property': {'id': t.property_id, 'name': t.property.name},
        'unit': t.unit.unit_number if t.unit else None,
        'move_in_date': t.move_in_date.isoformat() if t.move_in_date else None,
    }
    if full:
        data['move_out_date'] = t.move_out_date.isoformat() if t.move_out_date else None
        data['emergency_contact'] = t.emergency_contact
        data['emergency_phone'] = t.emergency_phone
        data['notes'] = t.notes
    return data


# ── Payments ──────────────────────────────────────────────────────────────────

@login_required
@require_GET
def api_payments(request):
    qs = Payment.objects.filter(property__owner=request.user).select_related('tenant', 'property')

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    property_id = request.GET.get('property_id')
    if property_id:
        qs = qs.filter(property_id=property_id)

    tenant_id = request.GET.get('tenant_id')
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    items, meta = _paginate(qs, request)
    return JsonResponse({
        'results': [_serialize_payment(p) for p in items],
        'meta': meta,
    })


@login_required
@require_GET
def api_payment_detail(request, payment_id):
    p = get_object_or_404(Payment, id=payment_id, property__owner=request.user)
    return JsonResponse(_serialize_payment(p, full=True))


def _serialize_payment(p, full=False):
    data = {
        'id': p.id,
        'amount': float(p.amount),
        'status': p.status,
        'status_label': p.get_status_display(),
        'payment_date': p.payment_date.isoformat(),
        'due_date': p.due_date.isoformat(),
        'payment_method': p.payment_method,
        'reference_number': p.reference_number,
        'tenant': {'id': p.tenant_id, 'name': f"{p.tenant.first_name} {p.tenant.last_name}"},
        'property': {'id': p.property_id, 'name': p.property.name},
    }
    if full:
        data['notes'] = p.notes
        data['created_at'] = p.created_at.isoformat()
    return data


# ── Maintenance ───────────────────────────────────────────────────────────────

@login_required
@require_GET
def api_maintenance(request):
    qs = MaintenanceRequest.objects.filter(property__owner=request.user).select_related('property', 'tenant', 'unit')

    status = request.GET.get('status')
    if status:
        qs = qs.filter(status=status)

    priority = request.GET.get('priority')
    if priority:
        qs = qs.filter(priority=priority)

    property_id = request.GET.get('property_id')
    if property_id:
        qs = qs.filter(property_id=property_id)

    items, meta = _paginate(qs, request)
    return JsonResponse({
        'results': [_serialize_maintenance(r) for r in items],
        'meta': meta,
    })


@login_required
@require_GET
def api_maintenance_detail(request, request_id):
    r = get_object_or_404(MaintenanceRequest, id=request_id, property__owner=request.user)
    return JsonResponse(_serialize_maintenance(r, full=True))


# ── SMS Reminders ─────────────────────────────────────────────────────────────

# ── Notifications ─────────────────────────────────────────────────────────────

@login_required
@require_GET
def api_notifications(request):
    today = timezone.now().date()

    overdue = Payment.objects.filter(
        tenant__property__owner=request.user,
        due_date__lt=today,
        status__in=['failed', 'pending']
    ).select_related('tenant', 'tenant__property').order_by('due_date')

    pending_maint = MaintenanceRequest.objects.filter(
        property__owner=request.user, status='pending'
    ).select_related('property', 'tenant').order_by('reported_date')

    items = []
    for p in overdue:
        days = (today - p.due_date).days
        items.append({
            'type': 'payment',
            'icon': 'fa-money-bill-wave',
            'color': 'red',
            'title': f'Malipo: {p.tenant.first_name} {p.tenant.last_name}',
            'message': f'Ksh {p.amount:,.0f} — siku {days} zimepita',
            'url': f'/dashboard/payments/{p.id}/',
        })

    for r in pending_maint:
        items.append({
            'type': 'maintenance',
            'icon': 'fa-tools',
            'color': 'amber',
            'title': f'Matengenezo: {r.property.name}',
            'message': r.description[:80] if r.description else 'Hakuna maelezo',
            'url': f'/dashboard/maintenance/{r.id}/',
        })

    return JsonResponse({'items': items, 'count': len(items)})


@login_required
@require_POST
@csrf_exempt
def api_payment_remind(request, payment_id):
    p = get_object_or_404(Payment, id=payment_id, property__owner=request.user)
    ok = send_payment_reminder(p.tenant, p)
    print(f"Reminder sent to {p.tenant.phone}: {ok}")
    return JsonResponse({'success': ok, 'phone': p.tenant.phone})


@login_required
@require_POST
@csrf_exempt
def api_maintenance_notify(request, request_id):
    r = get_object_or_404(MaintenanceRequest, id=request_id, property__owner=request.user)
    ok = send_maintenance_update(r.tenant, r)
    return JsonResponse({'success': ok, 'phone': r.tenant.phone})


def _serialize_maintenance(r, full=False):
    data = {
        'id': r.id,
        'title': r.title,
        'status': r.status,
        'status_label': r.get_status_display(),
        'priority': r.priority,
        'priority_label': r.get_priority_display(),
        'property': {'id': r.property_id, 'name': r.property.name},
        'unit': r.unit.unit_number,
        'tenant': {'id': r.tenant_id, 'name': f"{r.tenant.first_name} {r.tenant.last_name}"},
        'reported_date': r.reported_date.isoformat(),
        'cost': float(r.cost) if r.cost else None,
    }
    if full:
        data['description'] = r.description
        data['completed_date'] = r.completed_date.isoformat() if r.completed_date else None
    return data
