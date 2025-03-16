from django.db.models import Sum
from rest_framework import serializers
from .models import Profile
from accounts.models import User
from publications.serializers import PublicationSerializer
from publications.serializers import DonationSerializer
from datetime import date


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    age = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    publications = PublicationSerializer(many=True, read_only=True, source="user.publications")
    latest_donations = serializers.SerializerMethodField()
    total_profile_views = serializers.SerializerMethodField()
    total_publications = serializers.SerializerMethodField()
    total_donations = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'email', 'first_name', 'last_name',
            'country', 'city', 'phone_number', 'bio',
            'instagram', 'whatsapp', 'facebook', 'telegram',
            'birth_date', 'age',
            'avatar','date_joined', 'publications', 'latest_donations',
            'total_profile_views',
            'total_publications', 'total_donations'
        ]

    def get_age(self, obj):
        if obj.birth_date:
            today = date.today()
            return today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        return None

    def get_latest_donations(self, obj):
        donations = obj.user.publications.prefetch_related('donations').values('donations__donor_name',
                'donations__donor_amount','donations__created_at').order_by('-donations__created_at')[:5]
        return donations

    def get_total_publications(self, obj):
        return obj.user.publications.count()

    def get_total_donations(self, obj):
        return obj.user.publications.aggregate(total=Sum('donations__donor_amount'))['total'] or 0

    def get_total_profile_views(self, obj):
        return obj.views.count()

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     request = self.context.get('request')
    #
    #     if request and request.user != instance.user:
    #         data.pop('email', None)  # Скрываем email
    #         data.pop('phone_number', None)  # Скрываем телефон
    #     return data