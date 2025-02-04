from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'phone_number', 'birth_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'city', 'country', 'phone_number')
    list_filter = ('country', 'city', 'birth_date')
    ordering = ('user',)
    readonly_fields = ('calculate_age',)

    fieldsets = (
        ('User Information', {'fields': ('user',)}),
        ('Personal Details', {'fields': ('country', 'city', 'phone_number', 'bio', 'birth_date', 'calculate_age')}),
        ('Social Media', {'fields': ('instagram', 'whatsapp', 'facebook', 'telegram')}),
        ('Profile Picture', {'fields': ('avatar',)}),
    )

    def calculate_age(self, obj):
        return obj.calculate_age() if obj.birth_date else None
    calculate_age.short_description = 'Age'


admin.site.register(Profile, ProfileAdmin)
