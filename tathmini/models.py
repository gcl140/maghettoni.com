from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
import random
import string

class PhoneVerification(models.Model):
    phone = models.CharField(max_length=20, unique=True, verbose_name="Phone Number")
    verification_code = models.CharField(max_length=6, verbose_name="Verification Code")
    is_verified = models.BooleanField(default=False, verbose_name="Is Verified")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    expires_at = models.DateTimeField(verbose_name="Expires At")
    
    class Meta:
        verbose_name = "Phone Verification"
        verbose_name_plural = "Phone Verifications"
    
    def __str__(self):
        return f"{self.phone} - {self.verification_code}"
    
    def is_expired(self):
        """Check if verification code has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @classmethod
    def generate_code(cls, length=6):
        """Generate random verification code"""
        return ''.join(random.choices(string.digits, k=length))

class AssessmentSubmission(models.Model):
    CURRENT_SITUATION_CHOICES = [
        ('notebooks', 'I manage using notebooks'),
        ('computer_systems', 'I manage using different computer systems'),
        ('delegated_manager', 'I delegated someone to help me manage'),
    ]
    
    GOALS_CHOICES = [
        ('self_manage', 'Manage my properties myself with a good system'),
        ('delegate_with_visibility', 'Delegate management while staying directly involved through a system'),
    ]
    
    CHALLENGE_CHOICES = [
        ('record_keeping', 'Difficulty keeping records'),
        ('late_rent', 'Tenants paying rent late'),
        ('slow_growth', 'Rental business growing slowly'),
        ('high_maintenance_costs', 'High maintenance and repair costs'),
        ('limited_time', 'Lack of time to manage properly'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Full Name")
    email = models.EmailField(validators=[EmailValidator()], verbose_name="Email")
    location = models.CharField(max_length=255, verbose_name="Location")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Phone Number")
    
    current_situation = models.CharField(
        max_length=20,
        choices=CURRENT_SITUATION_CHOICES,
        verbose_name="Current Situation"
    )
    
    goals = models.CharField(
        max_length=50,
        choices=GOALS_CHOICES,
        verbose_name="Goals"
    )
    
    challenges = models.TextField(verbose_name="Challenges")
    solution = models.TextField(verbose_name="Suggested Solution", blank=True)
    
    submitted_at = models.DateTimeField(default=timezone.now, verbose_name="Submitted At")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    verified_phone = models.ForeignKey(
        PhoneVerification, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Verified Phone"
    )
    
    class Meta:
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.name} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_challenges_list(self):
        """Return challenges as list"""
        return self.challenges.split(',') if self.challenges else []
    
    def get_current_situation_label(self):
        """Get display label for current situation."""
        choices_dict = dict(self.CURRENT_SITUATION_CHOICES)
        return choices_dict.get(self.current_situation, '')
    
    def get_goals_label(self):
        """Get display label for goals."""
        choices_dict = dict(self.GOALS_CHOICES)
        return choices_dict.get(self.goals, '')
    
class Subscriber(models.Model):
    email = models.EmailField(unique=True, validators=[EmailValidator()], verbose_name="Email")
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="Subscribed At")
    
    class Meta:
        verbose_name = "Subscriber"
        verbose_name_plural = "Subscribers"
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email