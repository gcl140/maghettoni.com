from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
import random
import string

class PhoneVerification(models.Model):
    phone = models.CharField(max_length=20, unique=True, verbose_name="Nambari Ya Simu")
    verification_code = models.CharField(max_length=6, verbose_name="Msimbo Wa Uthibitisho")
    is_verified = models.BooleanField(default=False, verbose_name="Imehakikiwa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Imeundwa")
    expires_at = models.DateTimeField(verbose_name="Inaisha")
    
    class Meta:
        verbose_name = "Uthibitisho Wa Simu"
        verbose_name_plural = "Uthibitisho Wa Simu"
    
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
        ('madaftari', 'Nasimamia kutumia madaftari'),
        ('kompyuta', 'Nasimamia kutumia mifumo mbalimbali ya kompyuta'),
        ('mkabidhi', 'Nimemkabidhi mtu anisaidie kusimamia'),
    ]
    
    GOALS_CHOICES = [
        ('kusimamia-mwenyewe', 'Kusimamia nyumba zangu mwenyewe nikiwa na mfumo mzuri'),
        ('kukabidhi-mtu', 'Kukabidhi mtu asimamie nyumba yangu huku nikiwa na mfumo unaonihusha moja kwa moja'),
    ]
    
    CHALLENGE_CHOICES = [
        ('ugumu-rekodi', 'Ugumu wa kutunza rekodi zako'),
        ('wachelewa-kulipa', 'Wapangaji kuchelewa kulipa kodi'),
        ('kukua-taratibu', 'Biashara yako ya nyumba za kupanga kukua taratibu'),
        ('gharama-kubwa', 'Gharama kubwa za ukarabati na matengenezo'),
        ('ukosefu-wakati', 'Ukosefu wa wakati wa kusimamia vyema'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Jina Kamili")
    email = models.EmailField(validators=[EmailValidator()], verbose_name="Barua Pepe")
    location = models.CharField(max_length=255, verbose_name="Mahali Unapoishi")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Nambari Ya Simu")
    
    current_situation = models.CharField(
        max_length=20,
        choices=CURRENT_SITUATION_CHOICES,
        verbose_name="Hali Ya Sasa"
    )
    
    goals = models.CharField(
        max_length=50,
        choices=GOALS_CHOICES,
        verbose_name="Malengo"
    )
    
    challenges = models.TextField(verbose_name="Changamoto")
    solution = models.TextField(verbose_name="Njia Ya Kusaidia", blank=True)
    
    submitted_at = models.DateTimeField(default=timezone.now, verbose_name="Tarehe Ya Kutuma")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Anwani Ya IP")
    verified_phone = models.ForeignKey(
        PhoneVerification, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Simu Iliyohakikiwa"
    )
    
    class Meta:
        verbose_name = "Tathmini"
        verbose_name_plural = "Tathmini"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.name} - {self.submitted_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_challenges_list(self):
        """Return challenges as list"""
        return self.challenges.split(',') if self.challenges else []
    
    def get_current_situation_display_sw(self):
        """Get Swahili display for current situation"""
        choices_dict = dict(self.CURRENT_SITUATION_CHOICES)
        return choices_dict.get(self.current_situation, '')
    
    def get_goals_display_sw(self):
        """Get Swahili display for goals"""
        choices_dict = dict(self.GOALS_CHOICES)
        return choices_dict.get(self.goals, '')
    
class Subscriber(models.Model):
    email = models.EmailField(unique=True, validators=[EmailValidator()], verbose_name="Barua Pepe")
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="Imejisajili")
    
    class Meta:
        verbose_name = "Mteja Aliyejisajili"
        verbose_name_plural = "Wateja Waliyojisajili"
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email