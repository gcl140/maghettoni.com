import random
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Official Email", blank=True, null=True)
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    telephone = models.CharField(max_length=13, unique=True, verbose_name="Telephone Number", blank=True, null=True)
    about = models.TextField(blank=True, null=True, verbose_name="About")

    is_landlord = models.BooleanField(
        default=False,
        verbose_name="Is Landlord",
        help_text="Grants access to the landlord dashboard. Set by admin.",
    )

    # Verification gate — landlords must be set to True by admin before they can log in.
    # Tenant accounts are created via invite and set to True automatically.
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Is Verified",
        help_text="Landlords must be verified by admin. Tenant accounts are verified automatically on invite acceptance.",
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username}"


class OTPVerification(models.Model):
    """One-Time Passwords for phone verification (assessment form & auth)."""
    phone = models.CharField(max_length=25)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    @classmethod
    def generate(cls, phone: str) -> 'OTPVerification':
        code = f"{random.randint(100000, 999999)}"
        return cls.objects.create(phone=phone, code=code)

    def __str__(self):
        return f"OTP {self.phone} — {'used' if self.is_used else 'pending'}"
