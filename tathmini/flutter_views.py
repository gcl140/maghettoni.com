"""
Flutter / mobile API endpoints for the tathmini (onboarding) app.
Copied from views.py — web URLs still point to views.py, Flutter URLs point here.
These are public endpoints (no auth required).
"""
import json
import logging
import random

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from datetime import timedelta

from dashboardd.services import send_otp
from .models import AssessmentSubmission, PhoneVerification

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


@csrf_exempt
@require_POST
def send_verification_code(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        if not phone:
            return JsonResponse({'success': False, 'error': 'Tafadhali ingiza nambari ya simu'}, status=400)

        verification_code = PhoneVerification.generate_code()
        PhoneVerification.objects.filter(phone=phone).delete()
        PhoneVerification.objects.create(
            phone=phone,
            verification_code=verification_code,
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        sent = send_otp(phone, verification_code)
        if not sent:
            return JsonResponse({'success': False, 'error': 'Imeshindwa kutuma ujumbe. Tafadhali jaribu tena.'}, status=500)
        return JsonResponse({'success': True, 'message': 'Msimbo umepelekwa kwenye simu yako.', 'expires_in': 10})
    except Exception as e:
        logger.error(f"send_verification_code: {e}")
        return JsonResponse({'success': False, 'error': 'Hitilafu imetokea. Tafadhali jaribu tena.'}, status=500)


@csrf_exempt
@require_POST
def verify_phone_code(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        code  = data.get('code', '').strip()
        if not phone or not code:
            return JsonResponse({'success': False, 'error': 'Tafadhali ingiza nambari ya simu na msimbo'}, status=400)
        try:
            verification = PhoneVerification.objects.get(phone=phone, verification_code=code)
            if verification.is_expired():
                return JsonResponse({'success': False, 'error': 'Msimbo umeisha muda wake. Tafadhali omba msimbo mpya.'}, status=400)
            verification.is_verified = True
            verification.save()
            return JsonResponse({'success': True, 'message': 'Nambari ya simu imehakikiwa kikamilifu!', 'phone': phone})
        except PhoneVerification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Msimbo si sahihi au umeisha muda wake.'}, status=400)
    except Exception as e:
        logger.error(f"verify_phone_code: {e}")
        return JsonResponse({'success': False, 'error': 'Hitilafu imetokea. Tafadhali jaribu tena.'}, status=500)


@csrf_exempt
@require_GET
def check_phone_verified(request):
    phone = request.GET.get('phone', '').strip()
    if not phone:
        return JsonResponse({'success': False, 'error': 'Nambari ya simu haipo'}, status=400)
    try:
        verification = PhoneVerification.objects.get(phone=phone, is_verified=True)
        if verification.is_expired():
            return JsonResponse({'success': False, 'verified': False, 'message': 'Uthibitisho umeisha muda wake'})
        return JsonResponse({'success': True, 'verified': True, 'phone': phone})
    except PhoneVerification.DoesNotExist:
        return JsonResponse({'success': False, 'verified': False, 'message': 'Simu haijahakikiwa'})


@csrf_exempt
@require_POST
def submit_assessment(request):
    try:
        data = json.loads(request.body)
        for field in ['name', 'email', 'phone', 'current_situation', 'goals']:
            if not data.get(field):
                return JsonResponse({'success': False, 'error': f'Tafadhali jaza {field}'}, status=400)
        try:
            validate_email(data['email'])
        except ValidationError:
            return JsonResponse({'success': False, 'error': 'Tafadhali andika barua pepe sahihi'}, status=400)

        phone = data['phone'].strip()
        session_verified = bool(request.session.get(f'otp_verified_{phone}'))
        verification = None
        try:
            verification = PhoneVerification.objects.get(phone=phone, is_verified=True)
            if verification.is_expired():
                return JsonResponse({'success': False, 'error': 'Uthibitisho wa simu umeisha muda wake. Tafadhali hakiki simu yako tena.'}, status=400)
        except PhoneVerification.DoesNotExist:
            if not session_verified:
                return JsonResponse({'success': False, 'error': 'Tafadhali hakiki nambari yako ya simu kabla ya kuendelea.'}, status=400)

        if AssessmentSubmission.objects.filter(phone=phone).exists():
            return JsonResponse({'success': False, 'error': 'Nambari ya simu hii tayari imesajiliwa. Tafadhali tumia nambari nyingine.'}, status=400)

        submission = AssessmentSubmission(
            name=data['name'],
            email=data['email'],
            location=data.get('location', ''),
            phone=phone,
            current_situation=data['current_situation'],
            goals=data['goals'],
            challenges=data.get('challenges', ''),
            solution=data.get('solution', ''),
            submitted_at=timezone.now(),
            ip_address=_get_client_ip(request),
            verified_phone=verification,
        )
        submission.save()
        request.session.pop(f'otp_verified_{phone}', None)
        logger.info(f"New assessment: {data['name']} ({data['email']}) — {phone}")

        messages = [
            "Hongera! Umejitolea kujenga biashara bora ya nyumba za kupanga! 🎉",
            "Asante kwa kujisajili! Sasa una njia rahisi ya kusimamia nyumba zako! 🏡✨",
            "Umefanikiwa kujisajili! Tutawasiliana nawe hivi karibuni kukupa maelezo zaidi! 🚀",
            "Ahsante! Ujasiri wako utaleta matokeo mazuri. Tutaungana nawe hivi punde! 💫",
        ]
        return JsonResponse({
            'success': True,
            'message': random.choice(messages),
            'submission_id': submission.id,
            'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Data si sahihi. Tafadhali jaribu tena.'}, status=400)
    except Exception as e:
        logger.error(f"submit_assessment: {e}")
        return JsonResponse({'success': False, 'error': 'Hitilafu imetokea kwenye mfumo. Tafadhali jaribu tena baadaye.'}, status=500)
