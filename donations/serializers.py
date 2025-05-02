from rest_framework import serializers
from .models import Donation

class DonationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    donor_id = serializers.SerializerMethodField()
    donor_name = serializers.SerializerMethodField()
    donor_avatar = serializers.SerializerMethodField()
    support_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Donation
        fields = ['id','donor_id','donor_name', 'donor_avatar','donor_amount',
                  'support_percentage', 'support_amount', 'total_amount', 'created_at']

    def get_donor_name(self, obj):
        return f"{obj.donor.first_name} {obj.donor.last_name}".strip() if obj.donor else "Anonymous"

    def get_donor_avatar(self, obj):
        request = self.context.get('request')
        if obj.donor and hasattr(obj.donor, 'profile') and obj.donor.profile.avatar:
            avatar_url = obj.donor.profile.avatar.url
            return request.build_absolute_uri(avatar_url) if request else avatar_url
        return None

    def get_donor_id(self, obj):
        return obj.donor.id if obj.donor else None