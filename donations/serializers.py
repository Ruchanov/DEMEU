from rest_framework import serializers
from .models import Donation

class DonationSerializer(serializers.ModelSerializer):
    donor_name = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = ['donor_name', 'donor_amount', 'created_at']

    def get_donor_name(self, obj):
        return f"{obj.donor.first_name} {obj.donor.last_name}".strip() if obj.donor else "Anonymous"