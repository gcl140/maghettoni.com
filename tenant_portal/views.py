import uuid
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dashboardd.models import MaintenanceRequest, Notification, Payment, Property, TenantInvite, Unit
from .forms import TenantMaintenanceForm, TenantPaymentForm
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

def tenant_required(view_func):
    """Decorator: user must be authenticated and have a linked Tenant profile."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request.user, 'tenant_profile') or request.user.tenant_profile is None:
            return render(request, 'tenant_portal/no_access.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped


def _next_due_date(tenant):
    """Calculate the next rent due date based on move-in day."""
    today = date.today()
    day = tenant.move_in_date.day
    # Try this month first
    try:
        candidate = today.replace(day=day)
    except ValueError:
        # e.g. day=31 in a short month — use last day
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        candidate = today.replace(day=last_day)

    if candidate < today:
        # Move to next month
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


def _stay_stats(tenant):
    today = date.today()
    start = tenant.move_in_date
    end = tenant.move_out_date or today
    delta = end - start
    months = (end.year - start.year) * 12 + (end.month - start.month)
    days_remaining = None
    if tenant.move_out_date:
        days_remaining = (tenant.move_out_date - today).days
    return {
        'start': start,
        'end': tenant.move_out_date,
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
    tenant = request.user.tenant_profile
    today = date.today()

    next_due = _next_due_date(tenant)
    days_until_due = (next_due - today).days

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

    stay = _stay_stats(tenant)

    unread_notifs = TenantNotification.objects.filter(tenant=tenant, is_read=False).count()

    return render(request, 'tenant_portal/dashboard.html', {
        'tenant': tenant,
        'next_due': next_due,
        'days_until_due': days_until_due,
        'recent_payments': recent_payments,
        'pending_maintenance': pending_maintenance,
        'total_paid_sum': total_paid_sum,
        'overdue_payments': overdue_payments,
        'stay': stay,
        'today': today,
        'unread_notifs': unread_notifs,
    })


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@tenant_required
def tenant_payments(request):
    tenant = request.user.tenant_profile
    payments = Payment.objects.filter(tenant=tenant).order_by('-payment_date')
    submissions = TenantPaymentSubmission.objects.filter(tenant=tenant).order_by('-created_at')[:10]
    return render(request, 'tenant_portal/payments.html', {
        'tenant': tenant,
        'payments': payments,
        'submissions': submissions,
    })


@tenant_required
def tenant_payment_initiate(request):
    tenant = request.user.tenant_profile
    monthly_rent = tenant.unit.monthly_rent if tenant.unit else None
    next_due = _next_due_date(tenant)

    if request.method == 'POST':
        form = TenantPaymentForm(request.POST)
        if form.is_valid():
            # Rate limit: block if there's an unresolved 'processing' submission in the last 5 minutes
            cutoff = timezone.now() - timedelta(minutes=5)
            if TenantPaymentSubmission.objects.filter(
                tenant=tenant, status='processing', created_at__gte=cutoff
            ).exists():
                messages.warning(request, 'Malipo yanashughulikiwa tayari. Tafadhali subiri kidogo.')
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
        initial = {'amount': monthly_rent} if monthly_rent else {}
        form = TenantPaymentForm(initial=initial)

    return render(request, 'tenant_portal/payment_initiate.html', {
        'tenant': tenant,
        'form': form,
        'monthly_rent': monthly_rent,
        'next_due': next_due,
    })


@tenant_required
def tenant_payment_process(request, token):
    tenant = request.user.tenant_profile
    submission = get_object_or_404(TenantPaymentSubmission, payment_token=token, tenant=tenant)

    if submission.status not in ('processing', 'initiated'):
        return redirect('tenant_payment_status', token=token)

    if request.method == 'POST' and request.POST.get('action') == 'confirm':
        today = date.today()
        next_due = _next_due_date(tenant)

        # Generate a short reference number
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
            'Malipo Yamewasilishwa',
            f'Malipo ya TZS. {submission.amount:,.0f} yamewasilishwa. Ref: {ref}. Inasubiri uthibitisho wa msimamizi.',
            notif_type='success',
        )
        # Notify landlord
        landlord = tenant.property.owner
        _notify_landlord(
            landlord,
            f'Malipo Mapya: {tenant.first_name} {tenant.last_name}',
            f'TZS. {submission.amount:,.0f} — Ref: {ref} — {tenant.property.name}',
        )

        messages.success(request, f'Malipo yamewasilishwa! Ref: {ref}')
        return redirect('tenant_payment_status', token=token)

    return render(request, 'tenant_portal/payment_process.html', {
        'tenant': tenant,
        'submission': submission,
    })


@tenant_required
def tenant_payment_status(request, token):
    tenant = request.user.tenant_profile
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
    tenant = request.user.tenant_profile
    requests_qs = MaintenanceRequest.objects.filter(tenant=tenant).order_by('-reported_date')
    return render(request, 'tenant_portal/maintenance.html', {
        'tenant': tenant,
        'maintenance_requests': requests_qs,
    })


@tenant_required
def tenant_maintenance_create(request):
    tenant = request.user.tenant_profile

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
                'Ombi la Matengenezo Limewasilishwa',
                f'Ombi lako: "{req.title}" limewasilishwa kwa msimamizi.',
                notif_type='info',
            )
            _notify_landlord(
                tenant.property.owner,
                f'Ombi Jipya la Matengenezo: {tenant.property.name}',
                f'{tenant.first_name} {tenant.last_name}: {req.title} ({req.get_priority_display()})',
            )
            messages.success(request, 'Ombi la matengenezo limewasilishwa!')
            return redirect('tenant_maintenance')
    else:
        form = TenantMaintenanceForm()

    return render(request, 'tenant_portal/maintenance_form.html', {
        'tenant': tenant,
        'form': form,
    })


@tenant_required
def tenant_maintenance_detail(request, request_id):
    tenant = request.user.tenant_profile
    req = get_object_or_404(MaintenanceRequest, id=request_id, tenant=tenant)
    return render(request, 'tenant_portal/maintenance_detail.html', {
        'tenant': tenant,
        'req': req,
    })


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@tenant_required
def tenant_profile(request):
    tenant = request.user.tenant_profile
    return render(request, 'tenant_portal/profile.html', {
        'tenant': tenant,
    })


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@tenant_required
def tenant_notifications(request):
    tenant = request.user.tenant_profile
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
    the Tenant record.  The landlord never sees this page or the token.
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
            # Use phone number as username (strip spaces/symbols for safety)
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
                is_verified=True,   # tenants are verified on invite acceptance
                is_tenant=True,     # marks this account as a tenant
            )

            # Link user ↔ tenant
            tenant.user = user
            tenant.status = 'active'
            tenant.save(update_fields=['user', 'status'])

            # Mark invite as used and wipe the temp password
            invite.is_used = True
            invite.temp_password = ''
            invite.save(update_fields=['is_used', 'temp_password'])

            # Log the tenant in immediately
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, f'Karibu, {tenant.first_name}! Akaunti yako imeanzishwa.')
            return redirect('tenant_dashboard')

    return render(request, 'tenant_portal/invite_accept.html', {
        'invite': invite,
        'tenant': tenant,
        'error': error,
    })
