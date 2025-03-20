from django.contrib import admin
from .models import Donation

class DonationAdmin(admin.ModelAdmin):
    list_display = ['get_donor_name', 'donor_amount', 'support_amount', 'total_amount', 'publication', 'created_at']
    search_fields = ('donor__email', 'publication__title')
    list_filter = ('publication',)

    def get_donor_name(self, obj):
        if obj.donor:
            return f"{obj.donor.first_name} {obj.donor.last_name}".strip() or obj.donor.email
        return "Anonymous"

    get_donor_name.short_description = "Donor Name"

admin.site.register(Donation, DonationAdmin)