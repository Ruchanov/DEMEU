from rest_framework import serializers
from .models import Donation

class DonationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    donor_name = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = ['id','donor_name', 'donor_amount', 'support_percentage', 'support_amount', 'total_amount', 'created_at']

    def get_donor_name(self, obj):
        return f"{obj.donor.first_name} {obj.donor.last_name}".strip() if obj.donor else "Anonymous"