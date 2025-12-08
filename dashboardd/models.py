from django.db import models
# from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Property(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('condo', 'Condo'),
        ('townhouse', 'Townhouse'),
        ('commercial', 'Commercial'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=200)
    address = models.TextField()
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    units = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.address}"

class Unit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units_list')
    unit_number = models.CharField(max_length=50)
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    square_feet = models.IntegerField(null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    is_occupied = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['property', 'unit_number']
    
    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"

class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tenant_profile')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tenants')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_tenant')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    lease_start_date = models.DateField()
    lease_end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='pending')
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.reference_number} - {self.tenant.full_name()}"

class MaintenanceRequest(models.Model):
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_requests')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='maintenance_requests')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='maintenance_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=50, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    reported_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-reported_date']
    
    def __str__(self):
        return f"{self.title} - {self.property.name}"