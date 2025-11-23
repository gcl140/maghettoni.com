from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Custom admin actions
@admin.action(description='Activate selected users')
def activate_selected_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} user(s) activated.", messages.SUCCESS)

@admin.action(description='Deactivate selected users')
def deactivate_selected_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} user(s) deactivated.", messages.WARNING)

# Admin for CustomUser model
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'username', 'email', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email', 'username']
    ordering = ['username']
    actions = [activate_selected_users, deactivate_selected_users]  # <-- Custom actions added here

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'email',
                'is_active', 'is_staff',
            ),
        }),
    )

# Register CustomUser model
admin.site.register(CustomUser, CustomUserAdmin)
