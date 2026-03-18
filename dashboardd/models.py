import uuid
from datetime import timedelta
from builtins import property as builtin_property

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Property(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('business', 'Commercial / Business'),
        ('other', 'Other'),
    ]

    RESIDENTIAL_TYPES = {'house', 'apartment', 'other'}
    BUSINESS_TYPES = {'business'}
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=200)
    address = models.TextField()
    address_data = models.JSONField(null=True, blank=True)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    units = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='property_images/', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
    
    @builtin_property
    def primary_image(self):
        first = self.images.first()
        if first:
            return first.image
        return self.image  # fallback to legacy single-image field

    def __str__(self):
        return f"{self.name} - {self.address}"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return f"{self.property.name} — image {self.pk}"


class PropertyDocument(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='property_documents/%Y/%m/')
    notes = models.TextField(blank=True, default='')
    version = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='property_documents_uploaded',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        constraints = [
            models.UniqueConstraint(fields=['property', 'title', 'version'], name='uniq_property_document_version'),
        ]

    def __str__(self):
        return f"{self.property.name} - {self.title} v{self.version}"

    @builtin_property
    def file_extension(self):
        if not self.file or not self.file.name or '.' not in self.file.name:
            return ''
        return self.file.name.rsplit('.', 1)[1].lower()

    @builtin_property
    def is_image(self):
        return self.file_extension in {'jpg', 'jpeg', 'png', 'gif', 'webp'}

    @builtin_property
    def is_pdf(self):
        return self.file_extension == 'pdf'

    @builtin_property
    def document_type(self):
        if self.is_image:
            return 'image'
        if self.is_pdf:
            return 'pdf'
        if self.file_extension in {'doc', 'docx', 'txt'}:
            return 'doc'
        return 'other'

class Unit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units_list')
    unit_number = models.CharField(max_length=50)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    square_feet = models.IntegerField(null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    min_rental_months = models.PositiveIntegerField(
        default=1,
        help_text='Minimum number of months a tenant must pay upfront.',
        validators=[MinValueValidator(1)],
    )
    is_occupied = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    amenities = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['property', 'unit_number']
    
    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"

class Tenant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tenant_profiles')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='tenants')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_tenant')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    move_in_date = models.DateField()
    profile_picture = models.ImageField(upload_to='tenant_profiles/', null=True, blank=True)
    notes = models.TextField(blank=True)
    notifications_enabled = models.BooleanField(
        default=True,
        help_text='Send eligibility/move-out reminders for this tenancy. Disable when leaving.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Fedha Taslimu'),
        ('check', 'Hundi'),
        ('bank_transfer', 'Uhamishaji wa Benki'),
        ('credit_card', 'Kadi ya Mkopo'),
        ('mobile_money', 'Pesa za Simu'),
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
    landlord_confirmed = models.BooleanField(
        default=False,
        help_text="Landlord has confirmed physical receipt of this payment."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Methods that are confirmed automatically (digital — no manual receipt needed)
    DIGITAL_METHODS = {'mobile_money', 'bank_transfer', 'credit_card'}

    @builtin_property
    def needs_landlord_confirmation(self):
        """True when payment was made by hand and landlord hasn't confirmed yet."""
        return self.payment_method not in self.DIGITAL_METHODS and not self.landlord_confirmed
    
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
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-reported_date']
    
    def __str__(self):
        return f"{self.title} - {self.property.name}"
    

class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_for_user')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class TenantInvite(models.Model):
    """
    One-time invite sent to a tenant when the landlord adds them.
    The token is emailed to the tenant; clicking it lets them set their
    password and activates their portal account.  The landlord never sees
    the token or the temporary credentials.
    """
    tenant = models.OneToOneField(
        'Tenant', on_delete=models.CASCADE, related_name='invite'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # Temporary plaintext password stored only until the tenant accepts.
    # We keep it here so the email can include it; cleared on acceptance.
    temp_password = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    @classmethod
    def create_for_tenant(cls, tenant, hours: int = 72) -> 'TenantInvite':
        import secrets, string
        alphabet = string.ascii_letters + string.digits
        temp_pw = ''.join(secrets.choice(alphabet) for _ in range(14))
        # Delete any existing (re-invite)
        cls.objects.filter(tenant=tenant).delete()
        return cls.objects.create(
            tenant=tenant,
            temp_password=temp_pw,
            expires_at=timezone.now() + timedelta(hours=hours),
        )

    def __str__(self):
        return f"Invite for {self.tenant} ({'used' if self.is_used else 'pending'})"