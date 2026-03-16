from django.contrib import admin

from .models import TenantNotification, TenantPaymentSubmission


@admin.register(TenantPaymentSubmission)
class TenantPaymentSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'short_token',
        'tenant',
        'payment',
        'amount',
        'payment_method',
        'status',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'payment_token',
        'tenant__first_name',
        'tenant__last_name',
        'tenant__email',
        'reference',
        'phone_number',
        'payment__reference_number',
    )
    readonly_fields = ('payment_token', 'created_at', 'updated_at')
    autocomplete_fields = ('tenant', 'payment')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25

    @admin.display(description='Token')
    def short_token(self, obj):
        return str(obj.payment_token)[:8]


@admin.register(TenantNotification)
class TenantNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'tenant',
        'notification_type',
        'is_read',
        'created_at',
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = (
        'title',
        'message',
        'tenant__first_name',
        'tenant__last_name',
        'tenant__email',
    )
    autocomplete_fields = ('tenant',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25
