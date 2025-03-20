from django.db.models import Sum
from rest_framework import serializers

from favorites.models import FavoritePublication
from favorites.serializers import FavoritePublicationSerializer
from publications.models import Donation
from .models import Profile
from accounts.models import User
from publications.serializers import PublicationSerializer
from publications.serializers import DonationSerializer
from datetime import date


class ProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
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
    total_favorite_publications = serializers.SerializerMethodField()
    favorite_publications = serializers.SerializerMethodField()
    days_since_registration = serializers.SerializerMethodField()


    class Meta:
        model = Profile
        fields = [
            'user_id','email', 'first_name', 'last_name',
            'country', 'city', 'phone_number', 'bio',
            'instagram', 'whatsapp', 'facebook', 'telegram',
            'birth_date', 'age',
            'avatar','date_joined', 'days_since_registration', 'publications', 'latest_donations',
            'total_profile_views',
            'total_publications', 'total_donations',
            'total_favorite_publications', 'favorite_publications',
        ]

    def get_age(self, obj):
        if obj.birth_date:
            today = date.today()
            return today.year - obj.birth_date.year - ((today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
        return None

    # def get_latest_donations(self, obj):
    #     donations = Donation.objects.filter(donor=obj.user).order_by('-created_at')[:5]
    #     return DonationSerializer(donations, many=True).data

    def get_latest_donations(self, obj):
        donations = Donation.objects.filter(donor=obj.user).order_by('-created_at')[:5]
        return [
            {
                "donor_name": f"{donation.donor.first_name} {donation.donor.last_name}".strip() if donation.donor else "Anonymous",
                "donor_amount": donation.donor_amount,
                "publication_id": donation.publication.id,
                "publication_title": donation.publication.title,
                "publication_category": donation.publication.category,
                "publication_author": f"{donation.publication.author.first_name} {donation.publication.author.last_name}".strip(),
                "publication_created_at": donation.publication.created_at
            }
            for donation in donations
        ]

    def get_total_publications(self, obj):
        return obj.user.publications.count()

    def get_total_donations(self, obj):
        return obj.user.publications.aggregate(total=Sum('donations__donor_amount'))['total'] or 0

    def get_total_profile_views(self, obj):
        return obj.views.count()

    def get_total_favorite_publications(self, obj):
        return FavoritePublication.objects.filter(user=obj.user).count()

    def get_favorite_publications(self, obj):
        favorites = FavoritePublication.objects.filter(user=obj.user)
        return FavoritePublicationSerializer(favorites, many=True).data

    def get_days_since_registration(self, obj):
        if hasattr(obj, 'user') and hasattr(obj.user, 'date_joined') and obj.user.date_joined:
            return (date.today() - obj.user.date_joined.date()).days
        return None

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     request = self.context.get('request')
    #
    #     if request and request.user != instance.user:
    #         data.pop('email', None)  # Скрываем email
    #         data.pop('phone_number', None)  # Скрываем телефон
    #     return data