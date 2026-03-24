"""
Flutter / mobile API endpoints for the yuzzaz (auth) app.
All views here return JSON and are csrf_exempt.
Web views remain in views.py untouched.
"""
import json

from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

User = get_user_model()


# ── Login ─────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def api_login(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    identifier = data.get('username', '').strip()
    password   = data.get('password', '')

    user = User.objects.filter(
        Q(username=identifier) | Q(email=identifier) | Q(telephone=identifier)
    ).first()

    if not user or not user.check_password(password):
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

    if not user.is_active:
        return JsonResponse({'success': False, 'error': 'Account not activated'}, status=403)

    if not user.is_verified:
        return JsonResponse({'success': False, 'error': 'Account not verified'}, status=403)

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    is_landlord = not user.tenant_profiles.exists()
    return JsonResponse({
        'success': True,
        'is_landlord': is_landlord,
        'username': user.get_full_name() or user.username,
        'session_key': request.session.session_key,
    })


# ── Logout ────────────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def api_logout(request):
    request.session.flush()
    return JsonResponse({'success': True})
