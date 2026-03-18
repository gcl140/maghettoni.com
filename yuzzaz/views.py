# views.py
import json
import random
from datetime import timedelta, datetime

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from yuzzaz.forms import CustomUserForm, UserRegistrationForm
from yuzzaz.models import OTPVerification
from yuzzaz.tokens import account_activation_token
from dashboardd.services import send_otp as sms_send_otp

User = get_user_model()


MESSAGES = {
    'invalid_json': {
        'en': 'Invalid JSON',
        'sw': 'Data ya JSON si sahihi.',
    },
    'phone_required': {
        'en': 'Phone number is required.',
        'sw': 'Nambari ya simu inahitajika.',
    },
    'otp_rate_limited': {
        'en': 'Rate limit reached. Please wait one hour and try again.',
        'sw': 'Umefika kikomo. Tafadhali subiri saa moja na ujaribu tena.',
    },
    'otp_send_failed': {
        'en': 'Failed to send OTP. Check your phone number and try again.',
        'sw': 'Imeshindwa kutuma OTP. Angalia nambari yako na ujaribu tena.',
    },
    'otp_sent_for': {
        'en': 'OTP sent to {phone}',
        'sw': 'OTP imetumwa kwa {phone}',
    },
    'otp_data_incomplete': {
        'en': 'Phone and code are required.',
        'sw': 'Taarifa hazikamiliki.',
    },
    'otp_invalid_code': {
        'en': 'Invalid code.',
        'sw': 'Msimbo si sahihi.',
    },
    'otp_expired': {
        'en': 'Code has expired. Please request a new one.',
        'sw': 'Msimbo umekwisha muda. Tuma tena.',
    },
    'otp_verified': {
        'en': 'Phone number verified successfully!',
        'sw': 'Nambari imethibitishwa!',
    },
    'activation_link_invalid': {
        'en': 'Activation link is invalid.',
        'sw': 'Kiungo cha uamilishaji si sahihi.',
    },
    'account_already_active': {
        'en': 'Account is already activated. You can log in.',
        'sw': 'Akaunti tayari imeamilishwa. Unaweza kuingia.',
    },
    'activation_link_expired': {
        'en': 'Activation link is invalid or expired.',
        'sw': 'Kiungo cha uamilishaji si sahihi au kimeisha muda.',
    },
    'account_activated': {
        'en': 'Your account has been activated. You can log in now.',
        'sw': 'Akaunti yako imeamilishwa. Unaweza kuingia sasa.',
    },
    'no_activation_request': {
        'en': 'No activation request was found.',
        'sw': 'Hakuna ombi la uamilishaji lililopatikana.',
    },
    'activation_session_expired': {
        'en': 'Session expired. Please contact administrator.',
        'sw': 'Kipindi kimeisha. Tafadhali wasiliana na msimamizi.',
    },
    'activation_link_resent': {
        'en': 'A new activation link has been sent.',
        'sw': 'Kiungo kipya kimetumwa.',
    },
    'account_not_found': {
        'en': 'No account was found.',
        'sw': 'Hakuna akaunti iliyopatikana.',
    },
    'account_not_activated': {
        'en': 'Your account is not activated yet. Please check your email.',
        'sw': 'Akaunti yako haijamilishwa. Angalia barua pepe yako.',
    },
    'account_not_verified': {
        'en': 'Your account has not been approved yet. We will contact you soon.',
        'sw': 'Akaunti yako bado haijakubaliwa na timu yetu. Tutawasiliana nawe hivi karibuni.',
    },
    'login_success': {
        'en': 'Logged in successfully.',
        'sw': 'Umefanikiwa kuingia.',
    },
    'invalid_credentials': {
        'en': 'Invalid credentials, please try again.',
        'sw': 'Taarifa zako si sahihi, tafadhali jaribu tena.',
    },
    'logged_out': {
        'en': 'You have been logged out successfully.',
        'sw': 'Umetoka nje kikamilifu.',
    },
    'profile_updated': {
        'en': 'Your profile has been updated!',
        'sw': 'Wasifu wako umesasishwa!',
    },
    'phone_verify_first': {
        'en': 'Please verify your phone number first.',
        'sw': 'Thibiti nambari yako ya simu kwanza.',
    },
    'missing_required_fields': {
        'en': 'Missing required fields',
        'sw': 'Sehemu muhimu hazijajazwa',
    },
    'message_sent_success': {
        'en': 'Message sent successfully',
        'sw': 'Ujumbe umetumwa kikamilifu',
    },
}


def get_language(request, payload=None):
    """Resolve active language for this request: en or sw."""
    lang = None

    if isinstance(payload, dict):
        lang = payload.get('lang')

    if not lang:
        lang = request.GET.get('lang')

    if not lang and request.method == 'POST':
        lang = request.POST.get('lang')

    if not lang:
        lang = request.session.get('lang')

    if lang not in {'en', 'sw'}:
        accept = (request.headers.get('Accept-Language', '') or '').lower()
        lang = 'sw' if accept.startswith('sw') else 'en'

    request.session['lang'] = lang
    return lang


def msg(request, key, payload=None, **fmt):
    lang = get_language(request, payload)
    template = MESSAGES.get(key, {}).get(lang) or MESSAGES.get(key, {}).get('en') or key
    return template.format(**fmt) if fmt else template


# ─────────────────────────────────────────────────────────────────────────────
# Landing
# ─────────────────────────────────────────────────────────────────────────────

def landing(request):
    return render(request, 'yuzzaz/home.html', {'year': datetime.now().year})


# ─────────────────────────────────────────────────────────────────────────────
# Registration — CLOSED to the public
# ─────────────────────────────────────────────────────────────────────────────

def register(request):
    """Registration is invite-only / admin-onboarded.  Show info page."""
    return render(request, 'yuzzaz/register_closed.html')


# ─────────────────────────────────────────────────────────────────────────────
# OTP — phone verification for the assessment form
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def otp_send(request):
    """
    POST { "phone": "+255..." }
    Generates a 6-digit code, stores it, and sends via Beem SMS.
    Rate-limited to 3 requests per phone per hour.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': msg(request, 'invalid_json')}, status=400)

    phone = data.get('phone', '').strip()
    if not phone:
        return JsonResponse({'error': msg(request, 'phone_required', data)}, status=400)

    # Rate limit: max 3 OTPs per phone per hour
    hour_ago = timezone.now() - timedelta(hours=1)
    recent_count = OTPVerification.objects.filter(
        phone=phone, created_at__gte=hour_ago
    ).count()
    # if recent_count >= 3:
    #     return JsonResponse(
    #         {'error': msg(request, 'otp_rate_limited', data)},
    #         status=429,
    #     )

    otp = OTPVerification.generate(phone)
    print(f"OTP requested for phone: {phone} is {otp.code}")

    sent = sms_send_otp(phone, otp.code)
    if not sent:
        otp.delete()
        return JsonResponse(
            {'error': msg(request, 'otp_send_failed', data)},
            status=500,
        )

    return JsonResponse({'status': 'sent', 'message': msg(request, 'otp_sent_for', data, phone=phone)})


@csrf_exempt
@require_POST
def otp_verify(request):
    """
    POST { "phone": "+255...", "code": "123456" }
    Verifies the code.  On success, stamps the session so the assessment
    form submission can confirm the phone was verified.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': msg(request, 'invalid_json')}, status=400)

    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()

    if not phone or not code:
        return JsonResponse({'error': msg(request, 'otp_data_incomplete', data)}, status=400)

    otp = (
        OTPVerification.objects
        .filter(phone=phone, code=code, is_used=False)
        .order_by('-created_at')
        .first()
    )

    if not otp:
        return JsonResponse({'verified': False, 'error': msg(request, 'otp_invalid_code', data)}, status=400)

    if otp.is_expired():
        return JsonResponse(
            {'verified': False, 'error': msg(request, 'otp_expired', data)},
            status=400,
        )

    otp.is_used = True
    otp.save(update_fields=['is_used'])

    # Stamp the session so survey submission can verify
    request.session[f'otp_verified_{phone}'] = True

    return JsonResponse({'verified': True, 'message': msg(request, 'otp_verified', data)})


# ─────────────────────────────────────────────────────────────────────────────
# Email activation (kept for landlord accounts created by admin)
# ─────────────────────────────────────────────────────────────────────────────

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if not user:
        messages.error(request, msg(request, 'activation_link_invalid'))
        return redirect('home')

    if user.is_active:
        messages.info(request, msg(request, 'account_already_active'))
        return redirect('login')

    if not account_activation_token.check_token(user, token):
        messages.error(request, msg(request, 'activation_link_expired'))
        return redirect('home')

    user.is_active = True
    user.save()
    messages.success(request, msg(request, 'account_activated'))
    return redirect('login')


def activation_sent(request):
    email = request.session.get('inactive_user_email')
    if not email:
        messages.warning(request, msg(request, 'no_activation_request'))
        return redirect('login')

    if not request.session.get('email_sent_time'):
        request.session['email_sent_time'] = now().isoformat()

    return render(request, 'yuzzaz/activation_sent.html', {
        'email': email,
        'can_resend_at': now() + timedelta(seconds=90),
    })


def resend_activation_email(request):
    email = request.session.get('inactive_user_email')
    sent_time = request.session.get('email_sent_time')

    if not email or not sent_time:
        messages.error(request, msg(request, 'activation_session_expired'))
        return redirect('login')

    sent_time = datetime.fromisoformat(sent_time)
    user = User.objects.filter(email=email, is_active=False).first()
    if user:
        current_site_domain = request.get_host()
        message = render_to_string("yuzzaz/activate_account.html", {
            'user': user,
            'domain': current_site_domain,
            'protocol': 'https' if request.is_secure() else 'http',
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
            'current_year': datetime.now().year,
        })
        email_obj = EmailMessage("Activate your account", message, to=[user.email])
        email_obj.content_subtype = "html"
        email_obj.send()
        request.session['email_sent_time'] = now().isoformat()
        messages.success(request, msg(request, 'activation_link_resent'))
    else:
        messages.error(request, msg(request, 'account_not_found'))

    return redirect('activation_sent')


# ─────────────────────────────────────────────────────────────────────────────
# Login / Logout
# ─────────────────────────────────────────────────────────────────────────────

def login(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        from django.db.models import Q
        user = User.objects.filter(
            Q(username=identifier) | Q(email=identifier) | Q(telephone=identifier)
        ).first()
        if user and user.check_password(password):
            if not user.is_active:
                request.session['inactive_user_email'] = user.email
                request.session['email_sent_time'] = now().isoformat()
                messages.warning(
                    request,
                    msg(request, 'account_not_activated'),
                )
                return redirect('activation_sent')

            # ── Verification gate ──────────────────────────────────────────
            if not user.is_verified:
                messages.error(
                    request,
                    msg(request, 'account_not_verified'),
                )
                return render(request, 'yuzzaz/login.html')

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, msg(request, 'login_success'))

            # Tenant users go to the tenant portal
            if user.tenant_profiles.exists():
                return redirect('tenant_dashboard')
            return redirect('dashboard')

        messages.error(request, msg(request, 'invalid_credentials'))

    return render(request, 'yuzzaz/login.html')


def logout(request):
    auth_logout(request)
    messages.success(request, msg(request, 'logged_out'))
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def profile(request, user_id):
    from django.contrib.auth import update_session_auth_hash
    user = get_object_or_404(User, id=user_id)
    pw_error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_password' and user == request.user:
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
                return redirect('profile', user_id=user.id)
            form = CustomUserForm(instance=user)
        else:
            form = CustomUserForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, msg(request, 'profile_updated'))
                return redirect('profile', user_id=user.id)
    else:
        form = CustomUserForm(instance=user)

    return render(request, 'yuzzaz/profile.html', {
        'logged_in_user': request.user,
        'looking_at': user,
        'form': form,
        'pw_error': pw_error,
    })


def company_profile(request):
    return render(request, 'yuzzaz/company_profile.html', {})


def logout_and_login(request):
    auth_logout(request)
    return redirect(f"{reverse('social:begin', args=['google-oauth2'])}?next=/profile/")


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, msg(request, 'profile_updated'))
            return redirect('profile', user_id=request.user.id)
    else:
        form = CustomUserForm(instance=request.user)

    return render(request, 'yuzzaz/partials/edit_profile_modal.html', {
        'form': form,
        'viewing_user': request.user,
    })


@login_required
@require_POST
def set_language_preference(request):
    data = json.loads(request.body)
    lang = data.get('lang', 'en')
    if lang in ('en', 'sw'):
        request.user.preferred_language = lang
        request.user.save(update_fields=['preferred_language'])
    return JsonResponse({'ok': True})


def custom_404_view(request, exception):
    return render(request, 'partials/404.html', status=404)


# ─────────────────────────────────────────────────────────────────────────────
# Assessment / Contact forms
# ─────────────────────────────────────────────────────────────────────────────

@csrf_exempt
def send_gift_a_text(request):
    """
    Survey submission endpoint.
    Requires that the phone was OTP-verified in this session.
    """
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
        else:
            data = request.GET.dict()

        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        message_text = data.get('message', '').strip()

        if not all([name, email, message_text]):
            return JsonResponse({'status': 'error', 'message': msg(request, 'missing_required_fields', data)}, status=400)

        # ── OTP gate for survey submissions ──────────────────────────────
        if phone and not request.session.get(f'otp_verified_{phone}'):
            return JsonResponse(
                {'status': 'error', 'message': msg(request, 'phone_verify_first', data)},
                status=403,
            )

        subject = f'New Landlord Application from {name}'
        body = (
            f"Name: {name}\n"
            f"Phone: {phone}\n"
            f"Email: {email}\n\n"
            f"Message / Survey Answers:\n{message_text}"
        )
        EmailMessage(subject=subject, body=body, to=['christiangift44@gmail.com']).send(fail_silently=False)

        # Clear OTP verification from session after successful submission
        request.session.pop(f'otp_verified_{phone}', None)

        return JsonResponse({'status': 'success', 'message': msg(request, 'message_sent_success', data)})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': msg(request, 'invalid_json')}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def send_lissa_text(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
        else:
            data = request.GET.dict()

        name = data.get('name', 'Test User')
        phone = data.get('phone', '')
        email = data.get('email', 'test@example.com')
        message_text = data.get('message', '')

        if not all([name, email, message_text]):
            return JsonResponse({'status': 'error', 'message': msg(request, 'missing_required_fields', data)}, status=400)

        subject = f'New Message from {name}'
        body = f"Name: {name}\nPhone: {phone}\nEmail: {email}\n\nMessage:\n{message_text}"
        EmailMessage(subject=subject, body=body, to=['christiangift44@gmail.com']).send(fail_silently=False)

        return JsonResponse({'status': 'success', 'message': msg(request, 'message_sent_success', data)})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': msg(request, 'invalid_json')}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
