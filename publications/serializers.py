from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers
from datetime import date
from donations import models
from .models import Publication, PublicationImage, PublicationVideo, View, PublicationDocument
from profiles.models import Profile
from donations.models import Donation
from verification.tasks import process_document_verification


class PublicationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationImage
        fields = ['id', 'image']


class PublicationVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationVideo
        fields = ['id', 'video']


class DonationSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    donor_name = serializers.SerializerMethodField()

    class Meta:
        model = Donation
        fields = ['donor_name', 'donor_amount', 'avatar', 'created_at']

    def get_avatar(self, obj):
        if obj.donor and hasattr(obj.donor, 'profile') and obj.donor.profile.avatar:
            request = self.context.get('request')
            avatar_url = obj.donor.profile.avatar.url
            return request.build_absolute_uri(avatar_url) if request else avatar_url
        return None

    def get_donor_name(self, obj):
        return f"{obj.donor.first_name} {obj.donor.last_name}".strip() if obj.donor else "Anonymous"


class ViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = View
        fields = ['viewer', 'viewed_at']

class PublicationDocumentSerializer(serializers.ModelSerializer):
    preview = serializers.SerializerMethodField()

    class Meta:
        model = PublicationDocument
        fields = ['id', 'document_type', 'file', 'preview', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def get_preview(self, obj):
        if obj.file and obj.file.url.endswith(('jpg', 'jpeg', 'png')):
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None



class PublicationSerializer(serializers.ModelSerializer):
    images = PublicationImageSerializer(many=True, read_only=True)
    videos = PublicationVideoSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    uploaded_videos = serializers.ListField(child=serializers.FileField(), write_only=True, required=False)
    uploaded_documents = serializers.ListField(child=serializers.FileField(),write_only=True,required=False)
    uploaded_document_types = serializers.ListField(
        child=serializers.ChoiceField(choices=[('identity', 'Удостоверение личности'),
                                               ('income', 'Справка о доходах'),
                                               ('supporting', 'Подтверждающие документы')]),
        write_only=True,
        required=False
    )
    deleted_images = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    deleted_videos = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    delete_all_images = serializers.BooleanField(write_only=True, required=False, default=False)
    delete_all_videos = serializers.BooleanField(write_only=True, required=False, default=False)

    documents = PublicationDocumentSerializer(many=True, read_only=True)
    donations = serializers.SerializerMethodField()
    donation_percentage = serializers.SerializerMethodField()
    views = ViewSerializer(many=True, read_only=True)
    total_views = serializers.SerializerMethodField()
    total_donated = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    author_id = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    author_email = serializers.SerializerMethodField()
    author_avatar = serializers.SerializerMethodField()

    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            'id', 'author_id', 'author_name', 'author_email', 'author_avatar', 'title', 'category', 'description',
            'bank_details', 'amount', 'contact_name', 'contact_email',
            'contact_phone', 'created_at', 'updated_at', 'images',
            'videos', 'uploaded_images', 'uploaded_videos','uploaded_documents','uploaded_document_types',
            'deleted_images', 'deleted_videos', 'delete_all_images', 'delete_all_videos',
            'documents', 'donations', 'views', 'donation_percentage',
            'total_views', 'total_donated', 'total_comments','duration_days','days_remaining',]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author_id(self, obj):
        return obj.author.id if obj.author else None


    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}" if obj.author else None

    def get_author_email(self, obj):
        return obj.author.email if obj.author else None

    def get_author_avatar(self, obj):
        if obj.author and hasattr(obj.author, 'profile') and obj.author.profile.avatar:
            request = self.context.get('request')
            avatar_url = obj.author.profile.avatar.url
            return request.build_absolute_uri(avatar_url) if request else avatar_url
        return None


    def get_donations(self, obj):
        donations = obj.donations.select_related('donor')
        return [
            {
                "donor_name": f"{donation.donor.first_name} {donation.donor.last_name}".strip()
                if donation.donor else "Anonymous",
                "donor_amount": donation.donor_amount
            }
            for donation in donations
        ]

    def get_donation_percentage(self, obj):
        total_donations = obj.donations.aggregate(total=Sum('donor_amount'))['total'] or 0
        if obj.amount:
            return (total_donations / obj.amount) * 100
        return 0

    def get_total_views(self, obj):
        return obj.views.count()

    def get_total_donated(self, obj):
        return Donation.objects.filter(publication=obj).aggregate(total=Sum('donor_amount'))['total'] or 0

    def get_total_comments(self, obj):
        return obj.comments.count()

    def get_days_remaining(self, obj):
        if obj.expires_at:
            today = timezone.now().date()
            days = (obj.expires_at.date() - today).days
            return max(0, days)
        return None

    def validate_duration_days(self, value):
        if value not in [7, 14, 30]:
            raise serializers.ValidationError("Период публикации должен быть 7, 14 или 30 дней.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')

        if not request:
            raise serializers.ValidationError({"error": "Request object is missing in serializer context."})

        uploaded_images = request.FILES.getlist('uploaded_images')
        uploaded_videos = request.FILES.getlist('uploaded_videos')
        uploaded_documents = request.FILES.getlist('uploaded_documents')
        uploaded_document_types = request.data.getlist('uploaded_document_types[]')

        # Оставляем только поля, которые есть в модели Publication
        model_fields = {field.name for field in Publication._meta.fields}
        validated_data = {key: value for key, value in validated_data.items() if key in model_fields}

        publication = Publication.objects.create(**validated_data)

        for image in uploaded_images:
            PublicationImage.objects.create(publication=publication, image=image)
        print("Images uploaded successfully!" if uploaded_images else "No images uploaded!")

        for video in uploaded_videos:
            PublicationVideo.objects.create(publication=publication, video=video)
        print("Videos uploaded successfully!" if uploaded_videos else "No videos uploaded!")

        if uploaded_documents and len(uploaded_documents) != len(uploaded_document_types):
            raise serializers.ValidationError("Каждый документ должен иметь соответствующий тип.")

        for document, doc_type in zip(uploaded_documents, uploaded_document_types):
            publication_document = PublicationDocument.objects.create(
                publication=publication,file=document,document_type=doc_type)
            process_document_verification.delay(publication_document.id)

        return publication

    def update(self, instance, validated_data):
        # Получаем текущего пользователя
        request_user = self.context['request'].user

        # Проверяем, является ли пользователь автором публикации
        if instance.author != request_user:
            raise serializers.ValidationError({"error": "You do not have permission to edit this publication."})

        # Удаление конкретных изображений
        deleted_images = validated_data.pop('deleted_images', [])
        if deleted_images:
            images_to_delete = PublicationImage.objects.filter(id__in=deleted_images, publication=instance)
            images_to_delete.delete()

        # Удаление конкретных видео
        deleted_videos = validated_data.pop('deleted_videos', [])
        if deleted_videos:
            videos_to_delete = PublicationVideo.objects.filter(id__in=deleted_videos, publication=instance)
            videos_to_delete.delete()

        # Полное удаление всех изображений
        if validated_data.pop('delete_all_images', False):
            instance.images.all().delete()

        # Полное удаление всех видео
        if validated_data.pop('delete_all_videos', False):
            instance.videos.all().delete()

        # Добавление новых изображений
        uploaded_images = validated_data.pop('uploaded_images', [])
        for image in uploaded_images:
            PublicationImage.objects.create(publication=instance, image=image)

        # Добавление новых видео
        uploaded_videos = validated_data.pop('uploaded_videos', [])
        for video in uploaded_videos:
            PublicationVideo.objects.create(publication=instance, video=video)

        # Обновление остальных полей
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance