from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PasswordResetToken

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_verified', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Verification', {'fields': ('is_verified', 'verification_token_hash', 'verification_token_expiry')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'is_active')}),
        ('Security', {'fields': ('failed_attempts', 'lockout_time')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    filter_horizontal = ()
    readonly_fields = ('verification_token_expiry', 'failed_attempts', 'lockout_time')

class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    search_fields = ('user__email',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'expires_at')

admin.site.register(User, UserAdmin)
admin.site.register(PasswordResetToken, PasswordResetTokenAdmin)
