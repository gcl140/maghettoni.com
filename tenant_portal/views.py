import json
import uuid
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboardd.models import MaintenanceRequest, Notification, Payment, Property, Tenant, TenantInvite, Unit
from .forms import TenantMaintenanceForm, TenantPaymentForm, TenantProfileEditForm
from .models import TenantNotification, TenantPaymentSubmission

User = get_user_model()


def _notify_landlord(landlord, title, message):
    """Create a dashboardd Notification for the landlord (property owner), dedup 60s."""
    cutoff = timezone.now() - timedelta(seconds=60)
    if Notification.objects.filter(
        recipient=landlord, title=title, message=message, created_at__gte=cutoff
    ).exists():
        return
    Notification.objects.create(recipient=landlord, title=title, message=message)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tenant(user):
    """
    Return the primary Tenant for a user.
    With multi-tenancy support (user can have multiple Tenant records),
    prefer the most recently created active one.
    """
    qs = user.tenant_profiles.select_related('unit', 'property')
    active = qs.filter(status='active').order_by('-created_at').first()
    return active or qs.order_by('-created_at').first()


def tenant_required(view_func):
    """Decorator: user must be authenticated and have at least one linked Tenant record."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.tenant_profiles.exists():
            return render(request, 'tenant_portal/no_access.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


def _next_due_date(tenant):
    """Calculate the next rent due date based on move-in day."""
    today = date.today()
    day = tenant.move_in_date.day
    try:
        candidate = today.replace(day=day)
    except ValueError:
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        candidate = today.replace(day=last_day)

    if candidate < today:
        month = today.month + 1
        year = today.year
        if month > 12:
            month = 1
            year += 1
        try:
            candidate = date(year, month, day)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            candidate = date(year, month, last_day)
    return candidate


def _eligibility(tenant):
    """
    Returns dict with months_paid, eligible_until, and months_remaining
    based on completed payments vs monthly rent.
    """
    if not tenant.unit or not tenant.unit.monthly_rent:
        return None
    from django.db.models import Sum
    import calendar as _cal
    monthly_rent = tenant.unit.monthly_rent
    total_paid = tenant.payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    months_paid = int(total_paid / monthly_rent)
    if months_paid <= 0:
        return {
            'months_paid': 0, 'eligible_until': None, 'months_remaining': 0,
            'total_paid': total_paid, 'monthly_rent': monthly_rent,
            'days_left': None,
        }

    start = tenant.move_in_date
    m = start.month + months_paid - 1
    year = start.year + m // 12
    month = m % 12 + 1
    last_day = _cal.monthrange(year, month)[1]
    eligible_until = date(year, month, min(start.day, last_day))

    today = date.today()
    days_left = (eligible_until - today).days if eligible_until >= today else 0
    months_remaining = max(0, days_left // 30)

    return {
        'months_paid': months_paid,
        'eligible_until': eligible_until,
        'months_remaining': months_remaining,
        'days_left': days_left,
        'total_paid': total_paid,
        'monthly_rent': monthly_rent,
    }


def _stay_stats(tenant, eligible_until=None):
    """Build stay stats. Uses calculated eligible_until instead of stored move_out_date."""
    today = date.today()
    start = tenant.move_in_date
    end = eligible_until or today
    delta = end - start
    months = (end.year - start.year) * 12 + (end.month - start.month)
    days_remaining = (eligible_until - today).days if eligible_until else None
    return {
        'start': start,
        'end': eligible_until,
        'total_days': delta.days,
        'months': months,
        'days_remaining': days_remaining,
    }


def _tenant_notify(tenant, title, message, notif_type='info'):
    """Create a TenantNotification, skipping duplicates within 60 seconds."""
    cutoff = timezone.now() - timedelta(seconds=60)
    if TenantNotification.objects.filter(
        tenant=tenant, title=title, message=message, created_at__gte=cutoff
    ).exists():
        return
    TenantNotification.objects.create(
        tenant=tenant, title=title, message=message, notification_type=notif_type
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@tenant_required
def tenant_dashboard(request):
    tenant = _get_tenant(request.user)
    today = date.today()

    # Build per-tenancy due info for the countdown card.
    # "Next rent due" = eligible_until (when current paid period expires).
    all_active = request.user.tenant_profiles.filter(status='active').select_related('unit', 'property__owner')
    tenancies_due = []
    for t in all_active:
        elig = _eligibility(t)
        due = elig['eligible_until'] if elig and elig.get('eligible_until') else None
        days_left = (due - today).days if due else None
        tenancies_due.append({
            'next_due_iso': due.isoformat() if due else None,
            'days_until_due': days_left,
            'monthly_rent': float(t.unit.monthly_rent) if t.unit and t.unit.monthly_rent else None,
            'property_name': t.property.name if t.property else '',
            'unit_number': t.unit.unit_number if t.unit else '',
            'landlord': (t.property.owner.get_full_name() or t.property.owner.username) if t.property and t.property.owner else '',
            'move_in_date': t.move_in_date.strftime('%d %b %Y') if t.move_in_date else '',
        })
    if not tenancies_due:
        elig = _eligibility(tenant)
        due = elig['eligible_until'] if elig and elig.get('eligible_until') else None
        tenancies_due = [{
            'next_due_iso': due.isoformat() if due else None,
            'days_until_due': (due - today).days if due else None,
            'monthly_rent': float(tenant.unit.monthly_rent) if tenant.unit and tenant.unit.monthly_rent else None,
            'property_name': tenant.property.name if tenant.property else '',
            'unit_number': tenant.unit.unit_number if tenant.unit else '',
            'landlord': '',
            'move_in_date': tenant.move_in_date.strftime('%d %b %Y') if tenant.move_in_date else '',
        }]

    recent_payments = Payment.objects.filter(tenant=tenant).order_by('-payment_date')[:5]
    pending_maintenance = MaintenanceRequest.objects.filter(
        tenant=tenant, status__in=['pending', 'in_progress']
    ).order_by('-reported_date')[:5]

    total_paid = Payment.objects.filter(
        tenant=tenant, status='completed'
    ).values_list('amount', flat=True)
    total_paid_sum = sum(total_paid)

    overdue_payments = Payment.objects.filter(
        tenant=tenant, due_date__lt=today, status__in=['pending', 'failed']
    ).count()

    eligibility = _eligibility(tenant)
    stay = _stay_stats(tenant, eligible_until=eligibility['eligible_until'] if eligibility else None)

    unread_notifs = TenantNotification.objects.filter(tenant=tenant, is_read=False).count()

    return render(request, 'tenant_portal/dashboard.html', {
        'tenant': tenant,
        'tenancies_due_json': json.dumps(tenancies_due),
        'recent_payments': recent_payments,
        'pending_maintenance': pending_maintenance,
        'total_paid_sum': total_paid_sum,
        'overdue_payments': overdue_payments,
        'stay': stay,
        'today': today,
        'unread_notifs': unread_notifs,
        'eligibility': eligibility,
    })


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@tenant_required
def tenant_payments(request):
    tenant = _get_tenant(request.user)
    payments = Payment.objects.filter(tenant=tenant).order_by('-payment_date')
    submissions = TenantPaymentSubmission.objects.filter(tenant=tenant).order_by('-created_at')[:10]
    return render(request, 'tenant_portal/payments.html', {
        'tenant': tenant,
        'payments': payments,
        'submissions': submissions,
    })


@tenant_required
def tenant_payment_initiate(request):
    tenant = _get_tenant(request.user)
    unit = tenant.unit
    monthly_rent = unit.monthly_rent if unit else None
    min_months = unit.min_rental_months if unit else 1
    min_amount = monthly_rent * min_months if (monthly_rent and min_months > 1) else None
    next_due = _next_due_date(tenant)

    if request.method == 'POST':
        form = TenantPaymentForm(request.POST, unit=unit)
        if form.is_valid():
            cutoff = timezone.now() - timedelta(minutes=5)
            if TenantPaymentSubmission.objects.filter(
                tenant=tenant, status='processing', created_at__gte=cutoff
            ).exists():
                messages.warning(request, 'A payment is already being processed. Please wait a moment.')
                return redirect('tenant_payment_initiate')

            submission = TenantPaymentSubmission.objects.create(
                tenant=tenant,
                amount=form.cleaned_data['amount'],
                payment_method=form.cleaned_data['payment_method'],
                phone_number=form.cleaned_data.get('phone_number', ''),
                reference=form.cleaned_data.get('reference', ''),
                notes=form.cleaned_data.get('notes', ''),
                status='processing',
            )
            return redirect('tenant_payment_process', token=submission.payment_token)
    else:
        initial = {'amount': min_amount or monthly_rent} if monthly_rent else {}
        form = TenantPaymentForm(initial=initial, unit=unit)

    return render(request, 'tenant_portal/payment_initiate.html', {
        'tenant': tenant,
        'form': form,
        'monthly_rent': monthly_rent,
        'min_months': min_months,
        'min_amount': min_amount,
        'next_due': next_due,
    })


@tenant_required
def tenant_payment_process(request, token):
    tenant = _get_tenant(request.user)
    submission = get_object_or_404(TenantPaymentSubmission, payment_token=token, tenant=tenant)

    if submission.status not in ('processing', 'initiated'):
        return redirect('tenant_payment_status', token=token)

    if request.method == 'POST' and request.POST.get('action') == 'confirm':
        today = date.today()
        next_due = _next_due_date(tenant)
        ref = f"TP-{str(submission.payment_token).replace('-', '').upper()[:10]}"
        is_digital = submission.payment_method in Payment.DIGITAL_METHODS
        payment = Payment.objects.create(
            tenant=tenant,
            property=tenant.property,
            amount=submission.amount,
            payment_date=today,
            due_date=next_due,
            payment_method=submission.payment_method,
            status='completed' if is_digital else 'pending',
            landlord_confirmed=is_digital,
            reference_number=ref,
            notes=f"Submitted via Tenant Portal. {submission.notes}".strip('. '),
        )
        submission.payment = payment
        submission.status = 'submitted'
        submission.save(update_fields=['payment', 'status', 'updated_at'])

        _tenant_notify(
            tenant,
            'Payment Submitted',
            f'Payment of TZS. {submission.amount:,.0f} submitted. Ref: {ref}. Awaiting landlord confirmation.',
            notif_type='success',
        )
        landlord = tenant.property.owner
        _notify_landlord(
            landlord,
            f'New Payment: {tenant.first_name} {tenant.last_name}',
            f'TZS. {submission.amount:,.0f} — Ref: {ref} — {tenant.property.name}',
        )
        messages.success(request, f'Payment submitted! Ref: {ref}')
        return redirect('tenant_payment_status', token=token)

    return render(request, 'tenant_portal/payment_process.html', {
        'tenant': tenant,
        'submission': submission,
    })


@tenant_required
def tenant_payment_status(request, token):
    tenant = _get_tenant(request.user)
    submission = get_object_or_404(TenantPaymentSubmission, payment_token=token, tenant=tenant)
    return render(request, 'tenant_portal/payment_status.html', {
        'tenant': tenant,
        'submission': submission,
    })


# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

@tenant_required
def tenant_maintenance(request):
    tenant = _get_tenant(request.user)
    requests_qs = MaintenanceRequest.objects.filter(tenant=tenant).order_by('-reported_date')
    return render(request, 'tenant_portal/maintenance.html', {
        'tenant': tenant,
        'maintenance_requests': requests_qs,
    })


@tenant_required
def tenant_maintenance_create(request):
    tenant = _get_tenant(request.user)

    if not tenant.unit:
        messages.error(request, 'Huna chumba kilichopangwa. Wasiliana na msimamizi.')
        return redirect('tenant_maintenance')

    if request.method == 'POST':
        form = TenantMaintenanceForm(request.POST)
        if form.is_valid():
            req = MaintenanceRequest.objects.create(
                property=tenant.property,
                unit=tenant.unit,
                tenant=tenant,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                status='pending',
            )
            _tenant_notify(
                tenant,
                'Maintenance Request Submitted',
                f'Your request: "{req.title}" has been submitted to the landlord.',
                notif_type='info',
            )
            _notify_landlord(
                tenant.property.owner,
                f'New Maintenance Request: {tenant.property.name}',
                f'{tenant.first_name} {tenant.last_name}: {req.title} ({req.get_priority_display()})',
            )
            messages.success(request, 'Maintenance request submitted!')
            return redirect('tenant_maintenance')
    else:
        form = TenantMaintenanceForm()

    return render(request, 'tenant_portal/maintenance_form.html', {
        'tenant': tenant,
        'form': form,
    })


@tenant_required
def tenant_maintenance_detail(request, request_id):
    tenant = _get_tenant(request.user)
    req = get_object_or_404(MaintenanceRequest, id=request_id, tenant=tenant)
    return render(request, 'tenant_portal/maintenance_detail.html', {
        'tenant': tenant,
        'req': req,
    })


# ---------------------------------------------------------------------------
# Profile — multi-tenancy aware
# ---------------------------------------------------------------------------

@tenant_required
def tenant_profile(request):
    from django.contrib.auth import update_session_auth_hash
    tenant = _get_tenant(request.user)
    pw_error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_password':
            current = request.POST.get('current_password', '')
            new1 = request.POST.get('new_password1', '')
            new2 = request.POST.get('new_password2', '')
            if not request.user.check_password(current):
                pw_error = 'Current password is incorrect.'
            elif len(new1) < 8:
                pw_error = 'New password must be at least 8 characters.'
            elif new1 != new2:
                pw_error = 'New passwords do not match.'
            else:
                request.user.set_password(new1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
                return redirect('tenant_profile')
            form = TenantProfileEditForm(instance=tenant, user=request.user)
        else:
            form = TenantProfileEditForm(request.POST, request.FILES, instance=tenant, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('tenant_profile')
    else:
        form = TenantProfileEditForm(instance=tenant, user=request.user)

    # Build per-tenancy eligibility data for all tenancies of this user
    all_tenancies = list(
        request.user.tenant_profiles
        .select_related('unit', 'property', 'property__owner')
        .order_by('status', '-created_at')
    )
    tenancies_data = []
    for t in all_tenancies:
        el = _eligibility(t)
        tenancies_data.append({
            'tenant': t,
            'eligibility': el,
            'eligible_until': el['eligible_until'] if el else None,
            'days_left': el['days_left'] if el else None,
            'months_paid': el['months_paid'] if el else 0,
            'is_primary': t.pk == tenant.pk,
        })

    eligibility = _eligibility(tenant)
    stay = _stay_stats(tenant, eligible_until=eligibility['eligible_until'] if eligibility else None)

    return render(request, 'tenant_portal/profile.html', {
        'tenant': tenant,
        'form': form,
        'stay': stay,
        'pw_error': pw_error,
        'eligibility': eligibility,
        'tenancies_data': tenancies_data,
        'today': date.today(),
    })


@tenant_required
def tenant_edit_profile(request):
    tenant = _get_tenant(request.user)
    if request.method == 'POST':
        form = TenantProfileEditForm(request.POST, request.FILES, instance=tenant, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('tenant_profile')
    else:
        form = TenantProfileEditForm(instance=tenant, user=request.user)
    return render(request, 'tenant_portal/edit_profile.html', {
        'form': form,
        'tenant': tenant,
    })


@tenant_required
@require_POST
def toggle_tenancy_notifications(request, tenancy_id):
    """Toggle notifications_enabled for a specific tenancy belonging to this user."""
    tenancy = get_object_or_404(
        Tenant,
        pk=tenancy_id,
        user=request.user,
    )
    tenancy.notifications_enabled = not tenancy.notifications_enabled
    tenancy.save(update_fields=['notifications_enabled'])
    return JsonResponse({
        'ok': True,
        'enabled': tenancy.notifications_enabled,
        'tenancy_id': tenancy_id,
    })


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@tenant_required
def tenant_notifications(request):
    tenant = _get_tenant(request.user)
    notifs = TenantNotification.objects.filter(tenant=tenant)
    unread_ids = list(notifs.filter(is_read=False).values_list('id', flat=True))
    notifs_list = list(notifs[:30])
    if unread_ids:
        TenantNotification.objects.filter(id__in=unread_ids).update(is_read=True)
    return render(request, 'tenant_portal/notifications.html', {
        'tenant': tenant,
        'notifications': notifs_list,
    })


# ---------------------------------------------------------------------------
# Tenant Invite Accept  (no login required — this IS the onboarding entry)
# ---------------------------------------------------------------------------

def invite_accept(request, token):
    """
    Public view — the tenant clicks the invite link from their email.
    They set a new password; we create their User account and link it to
    the Tenant record.
    """
    invite = get_object_or_404(TenantInvite, token=token)

    if invite.is_used:
        return render(request, 'tenant_portal/invite_used.html', status=410)

    if invite.is_expired():
        return render(request, 'tenant_portal/invite_expired.html', {'invite': invite}, status=410)

    tenant = invite.tenant

    # If a user account already exists and is linked, redirect to login
    if tenant.user is not None:
        messages.info(request, 'Akaunti yako tayari imeanzishwa. Ingia hapa.')
        return redirect('login')

    error = None
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            error = 'Nenosiri lazima liwe na herufi 8 au zaidi.'
        elif password1 != password2:
            error = 'Manenosiri hayafanani. Jaribu tena.'
        else:
            base_username = ''.join(filter(str.isalnum, tenant.phone or '')) or tenant.email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=tenant.email or '',
                telephone=tenant.phone or '',
                password=password1,
                first_name=tenant.first_name,
                last_name=tenant.last_name,
                is_active=True,
                is_verified=True,
                is_tenant=True,
            )

            tenant.user = user
            tenant.status = 'active'
            tenant.save(update_fields=['user', 'status'])

            invite.is_used = True
            invite.temp_password = ''
            invite.save(update_fields=['is_used', 'temp_password'])

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, f'Karibu, {tenant.first_name}! Akaunti yako imeanzishwa.')
            return redirect('tenant_dashboard')

    return render(request, 'tenant_portal/invite_accept.html', {
        'invite': invite,
        'tenant': tenant,
        'error': error,
    })
