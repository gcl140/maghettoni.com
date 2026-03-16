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
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    phone = data.get('phone', '').strip()
    if not phone:
        return JsonResponse({'error': 'Nambari ya simu inahitajika.'}, status=400)

    # Rate limit: max 3 OTPs per phone per hour
    hour_ago = timezone.now() - timedelta(hours=1)
    recent_count = OTPVerification.objects.filter(
        phone=phone, created_at__gte=hour_ago
    ).count()
    if recent_count >= 3:
        return JsonResponse(
            {'error': 'Umefika kikomo. Tafadhali subiri saa moja na ujaribu tena.'},
            status=429,
        )

    otp = OTPVerification.generate(phone)
    sent = sms_send_otp(phone, otp.code)
    if not sent:
        otp.delete()
        return JsonResponse(
            {'error': 'Imeshindwa kutuma OTP. Angalia nambari yako na ujaribu tena.'},
            status=500,
        )

    return JsonResponse({'status': 'sent', 'message': f'OTP imetumwa kwa {phone}'})


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
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()

    if not phone or not code:
        return JsonResponse({'error': 'Taarifa hazikamiliki.'}, status=400)

    otp = (
        OTPVerification.objects
        .filter(phone=phone, code=code, is_used=False)
        .order_by('-created_at')
        .first()
    )

    if not otp:
        return JsonResponse({'verified': False, 'error': 'Msimbo si sahihi.'}, status=400)

    if otp.is_expired():
        return JsonResponse(
            {'verified': False, 'error': 'Msimbo umekwisha muda. Tuma tena.'},
            status=400,
        )

    otp.is_used = True
    otp.save(update_fields=['is_used'])

    # Stamp the session so survey submission can verify
    request.session[f'otp_verified_{phone}'] = True

    return JsonResponse({'verified': True, 'message': 'Nambari imethibitishwa!'})


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
        messages.error(request, "Kiungo cha uamilishaji si sahihi.")
        return redirect('home')

    if user.is_active:
        messages.info(request, "Akaunti tayari imeamilishwa. Unaweza kuingia.")
        return redirect('login')

    if not account_activation_token.check_token(user, token):
        messages.error(request, "Kiungo cha uamilishaji si sahihi au kimeisha muda.")
        return redirect('home')

    user.is_active = True
    user.save()
    messages.success(request, "Akaunti yako imeamilishwa. Unaweza kuingia sasa.")
    return redirect('login')


def activation_sent(request):
    email = request.session.get('inactive_user_email')
    if not email:
        messages.warning(request, "Hakuna ombi la uamilishaji lililopatikana.")
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
        messages.error(request, "Kipindi kimeisha. Tafadhali wasiliana na msimamizi.")
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
        messages.success(request, "Kiungo kipya kimetumwa.")
    else:
        messages.error(request, "Hakuna akaunti iliyopatikana.")

    return redirect('activation_sent')


# ─────────────────────────────────────────────────────────────────────────────
# Login / Logout
# ─────────────────────────────────────────────────────────────────────────────

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                request.session['inactive_user_email'] = user.email
                request.session['email_sent_time'] = now().isoformat()
                messages.warning(
                    request,
                    "Akaunti yako haijamilishwa. Angalia barua pepe yako.",
                )
                return redirect('activation_sent')

            # ── Verification gate ──────────────────────────────────────────
            if not user.is_verified:
                messages.error(
                    request,
                    "Akaunti yako bado haijakubaliwa na timu yetu. "
                    "Tutawasiliana nawe hivi karibuni.",
                )
                return render(request, 'yuzzaz/login.html')

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Umefanikiwa kuingia.")

            # Tenant users go to the tenant portal
            if hasattr(user, 'tenant_profile') and user.tenant_profile is not None:
                return redirect('tenant_dashboard')
            return redirect('dashboard')

        messages.error(request, "Taarifa zako si sahihi, tafadhali jaribu tena.")

    return render(request, 'yuzzaz/login.html')


def logout(request):
    auth_logout(request)
    messages.success(request, "Umetoka nje kikamilifu.")
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Wasifu wako umesasishwa!")
            return redirect('profile', user_id=user.id)
    else:
        form = CustomUserForm(instance=user)

    return render(request, 'yuzzaz/profile.html', {
        'logged_in_user': request.user,
        'looking_at': user,
        'form': form,
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
            messages.success(request, 'Wasifu umesasishwa!')
            return redirect('profile', user_id=request.user.id)
    else:
        form = CustomUserForm(instance=request.user)

    return render(request, 'yuzzaz/partials/edit_profile_modal.html', {
        'form': form,
        'viewing_user': request.user,
    })


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
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

        # ── OTP gate for survey submissions ──────────────────────────────
        if phone and not request.session.get(f'otp_verified_{phone}'):
            return JsonResponse(
                {'status': 'error', 'message': 'Thibiti nambari yako ya simu kwanza.'},
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

        return JsonResponse({'status': 'success', 'message': 'Message sent successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
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
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

        subject = f'New Message from {name}'
        body = f"Name: {name}\nPhone: {phone}\nEmail: {email}\n\nMessage:\n{message_text}"
        EmailMessage(subject=subject, body=body, to=['christiangift44@gmail.com']).send(fail_silently=False)

        return JsonResponse({'status': 'success', 'message': 'Message sent successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
