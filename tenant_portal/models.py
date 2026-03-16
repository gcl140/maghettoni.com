import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from dashboardd.models import Tenant, Payment

User = get_user_model()


class TenantPaymentSubmission(models.Model):
    PAYMENT_METHODS = [
        ('mobile_money', 'M-Pesa / Tigo Pesa / Airtel Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash (Deposit)'),
    ]
    STATUS_CHOICES = [
        ('initiated', 'Imeanza'),
        ('processing', 'Inashughulikiwa'),
        ('submitted', 'Imewasilishwa'),
        ('confirmed', 'Imethibitishwa'),
        ('failed', 'Imeshindwa'),
    ]

    payment_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payment_submissions')
    payment = models.OneToOneField(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='submission'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    phone_number = models.CharField(max_length=20, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {str(self.payment_token)[:8]} — {self.tenant}"


class TenantNotification(models.Model):
    NOTIF_TYPES = [
        ('info', 'Habari'),
        ('warning', 'Onyo'),
        ('success', 'Mafanikio'),
        ('danger', 'Hatari'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} → {self.tenant}"
