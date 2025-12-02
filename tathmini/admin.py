from django.contrib import admin
from .models import AssessmentSubmission, PhoneVerification

@admin.register(AssessmentSubmission)
class AssessmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'location', 'get_current_situation_display_sw', 'submitted_at')
    list_filter = ('current_situation', 'goals', 'submitted_at')
    search_fields = ('name', 'email', 'phone', 'location')
    readonly_fields = ('submitted_at', 'ip_address')
    fieldsets = (
        ('Taarifa Za Mtu', {
            'fields': ('name', 'email', 'phone', 'location')
        }),
        ('Tathmini', {
            'fields': ('current_situation', 'goals', 'challenges', 'solution')
        }),
        ('Taarifa Za Uwasilishaji', {
            'fields': ('submitted_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def get_current_situation_display_sw(self, obj):
        return obj.get_current_situation_display_sw()
    get_current_situation_display_sw.short_description = 'Hali Ya Sasa'
    
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