from django.contrib import admin
from .models import AssessmentSubmission, PhoneVerification, Subscriber

@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'location', 'get_current_situation_label', 'submitted_at')
    list_filter = ('current_situation', 'goals', 'submitted_at')
    search_fields = ('name', 'email', 'phone', 'location')
    readonly_fields = ('submitted_at', 'ip_address')
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone', 'location')
        }),
        ('Assessment', {
            'fields': ('current_situation', 'goals', 'challenges', 'solution')
        }),
        ('Submission Details', {
            'fields': ('submitted_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def get_current_situation_label(self, obj):
        return obj.get_current_situation_label()
    get_current_situation_label.short_description = 'Current Situation'
    
    def has_add_permission(self, request):
        return False  # Prevent adding submissions from admin
    
@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'is_verified', 'created_at', 'expires_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('phone',)
    readonly_fields = ('created_at', 'expires_at')
    
    def has_add_permission(self, request):
        return False  # Prevent adding verifications from admin
    

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)
    
    def has_add_permission(self, request):
        return False  # Prevent adding subscribers from admin