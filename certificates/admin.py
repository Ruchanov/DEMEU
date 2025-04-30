from django.contrib import admin
from .models import UserCertificate

@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'achieved_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
