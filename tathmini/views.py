from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import json
from .models import AssessmentSubmission, PhoneVerification
from django.utils import timezone
from datetime import timedelta
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def send_verification_code(request):
    """Send verification code to phone number"""
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        
        if not phone:
            return JsonResponse({
                'success': False,
                'error': 'Tafadhali ingiza nambari ya simu'
            }, status=400)
        
        # Generate verification code
        verification_code = PhoneVerification.generate_code()
        
        # Delete any existing verification for this phone
        PhoneVerification.objects.filter(phone=phone).delete()
        
        # Create new verification
        verification = PhoneVerification.objects.create(
            phone=phone,
            verification_code=verification_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # In production, you would send this code via SMS
        # For now, we'll log it and return it (remove this in production)
        logger.info(f"Verification code for {phone}: {verification_code}")
        
        return JsonResponse({
            'success': True,
            'message': 'Msimbo umepelekwa kwenye simu yako.',
            'code': verification_code,  # Remove this in production!
            'expires_in': 10  # minutes
        })
        
    except Exception as e:
        logger.error(f"Error sending verification code: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Hitilafu imetokea. Tafadhali jaribu tena.'
        }, status=500)

@csrf_exempt
@require_POST
def verify_phone_code(request):
    """Verify phone number with code"""
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()
        
        if not phone or not code:
            return JsonResponse({
                'success': False,
                'error': 'Tafadhali ingiza nambari ya simu na msimbo'
            }, status=400)
        
        try:
            verification = PhoneVerification.objects.get(phone=phone, verification_code=code)
            
            if verification.is_expired():
                return JsonResponse({
                    'success': False,
                    'error': 'Msimbo umeisha muda wake. Tafadhali omba msimbo mpya.'
                }, status=400)
            
            # Mark as verified
            verification.is_verified = True
            verification.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Nambari ya simu imehakikiwa kikamilifu!',
                'phone': phone
            })
            
        except PhoneVerification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Msimbo si sahihi au umeisha muda wake.'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error verifying phone: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Hitilafu imetokea. Tafadhali jaribu tena.'
        }, status=500)

@csrf_exempt
@require_POST
def submit_assessment(request):
    """API endpoint to handle form submission"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'current_situation', 'goals']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'Tafadhali jaza {field}'
                }, status=400)
        
        # Validate email
        try:
            validate_email(data['email'])
        except ValidationError:
            return JsonResponse({
                'success': False,
                'error': 'Tafadhali andika barua pepe sahihi'
            }, status=400)
        
        # Check if phone is verified
        phone = data['phone'].strip()
        try:
            verification = PhoneVerification.objects.get(phone=phone, is_verified=True)
            if verification.is_expired():
                return JsonResponse({
                    'success': False,
                    'error': 'Uthibitisho wa simu umeisha muda wake. Tafadhali hakiki simu yako tena.'
                }, status=400)
        except PhoneVerification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tafadhali hakiki nambari yako ya simu kabla ya kuendelea.'
            }, status=400)
        
        # Check if phone already exists (unique constraint)
        if AssessmentSubmission.objects.filter(phone=phone).exists():
            return JsonResponse({
                'success': False,
                'error': 'Nambari ya simu hii tayari imesajiliwa. Tafadhali tumia nambari nyingine.'
            }, status=400)
        
        # Create new submission
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
            ip_address=get_client_ip(request),
            verified_phone=verification
        )
        
        # Save to database
        submission.save()
        
        # Log the submission
        logger.info(f"New assessment submitted by {data['name']} ({data['email']}) - Phone: {phone}")
        
        # Return success response
        import random
        success_messages = [
            "Hongera! Umejitolea kujenga biashara bora ya nyumba za kupanga! 🎉",
            "Asante kwa kujisajili! Sasa una njia rahisi ya kusimamia nyumba zako! 🏡✨",
            "Umefanikiwa kujisajili! Tutawasiliana nawe hivi karibuni kukupa maelezo zaidi! 🚀",
            "Ahsante! Ujasiri wako utaleta matokeo mazuri. Tutaungana nawe hivi punde! 💫",
        ]
        
        return JsonResponse({
            'success': True,
            'message': random.choice(success_messages),
            'submission_id': submission.id,
            'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Data si sahihi. Tafadhali jaribu tena.'
        }, status=400)
    except Exception as e:
        logger.error(f"Error submitting assessment: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Hitilafu imetokea kwenye mfumo. Tafadhali jaribu tena baadaye.'
        }, status=500)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORLOADED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Check if phone is verified
@csrf_exempt
@require_GET
def check_phone_verified(request):
    """Check if phone number is verified"""
    phone = request.GET.get('phone', '').strip()
    
    if not phone:
        return JsonResponse({
            'success': False,
            'error': 'Nambari ya simu haipo'
        }, status=400)
    
    try:
        verification = PhoneVerification.objects.get(phone=phone, is_verified=True)
        
        if verification.is_expired():
            return JsonResponse({
                'success': False,
                'verified': False,
                'message': 'Uthibitisho umeisha muda wake'
            })
        
        return JsonResponse({
            'success': True,
            'verified': True,
            'phone': phone
        })
        
    except PhoneVerification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'verified': False,
            'message': 'Simu haijahakikiwa'
        })
    

@login_required
def assessment_dashboard(request):
    """View to see all submissions (admin only)"""
    submissions = AssessmentSubmission.objects.all().order_by('-submitted_at')
    
    # Statistics
    total_submissions = submissions.count()
    by_situation = {}
    by_goals = {}
    
    for sub in submissions:
        by_situation[sub.get_current_situation_display_sw()] = by_situation.get(sub.get_current_situation_display_sw(), 0) + 1
        by_goals[sub.get_goals_display_sw()] = by_goals.get(sub.get_goals_display_sw(), 0) + 1
    
    context = {
        'submissions': submissions,
        'total_submissions': total_submissions,
        'by_situation': by_situation,
        'by_goals': by_goals,
    }
    
    return render(request, 'assessment/dashboard.html', context)