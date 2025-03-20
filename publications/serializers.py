from django.db.models import Sum, F
from rest_framework import serializers
from .models import Publication, PublicationImage, PublicationVideo, Donation, View, PublicationDocument
from profiles.models import Profile


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

    class Meta:
        model = Publication
        fields = [
            'id', 'author_id', 'author_name', 'author_email', 'author_avatar', 'title', 'category', 'description',
            'bank_details', 'amount', 'contact_name', 'contact_email',
            'contact_phone', 'created_at', 'updated_at', 'images',
            'videos', 'uploaded_images', 'uploaded_videos','uploaded_documents','uploaded_document_types',
            'documents', 'donations', 'views', 'donation_percentage',
            'total_views', 'total_donated', 'total_comments']
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
        return obj.donations.aggregate(total=Sum('donor_amount'))['total'] or 0

    def get_total_comments(self, obj):
        return obj.comments.count()

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        uploaded_videos = validated_data.pop('uploaded_videos', [])
        uploaded_documents = validated_data.pop('uploaded_documents', [])
        uploaded_document_types = validated_data.pop('uploaded_document_types', [])

        if uploaded_documents and len(uploaded_documents) != len(uploaded_document_types):
            raise serializers.ValidationError("Каждый документ должен иметь соответствующий тип.")

        publication = Publication.objects.create(**validated_data)

        # Save images
        for image in uploaded_images:
            PublicationImage.objects.create(publication=publication, image=image)

        # Save videos
        for video in uploaded_videos:
            PublicationVideo.objects.create(publication=publication, video=video)

        for document, doc_type in zip(uploaded_documents, uploaded_document_types):
            PublicationDocument.objects.create(publication=publication, file=document, document_type=doc_type)

        return publication

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        uploaded_videos = validated_data.pop('uploaded_videos', [])

        update_images = validated_data.pop('update_images', 'add')  # 'add' or 'replace'
        update_videos = validated_data.pop('update_videos', 'add')  # 'add' or 'replace'


        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Обновление изображений
        if update_images == 'replace' and uploaded_images:  # Удаляем только если есть новые файлы
            instance.images.all().delete()
        for image in uploaded_images:
            PublicationImage.objects.create(publication=instance, image=image)

        # Обновление видео
        if update_videos == 'replace' and uploaded_videos:  # Удаляем только если есть новые файлы
            instance.videos.all().delete()
        for video in uploaded_videos:
            PublicationVideo.objects.create(publication=instance, video=video)

        return instance