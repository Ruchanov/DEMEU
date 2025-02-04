from rest_framework import serializers
from .models import Feedback, FeedbackImage

class FeedbackImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackImage
        fields = ['id', 'image']

class FeedbackSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    images = FeedbackImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)

    class Meta:
        model = Feedback
        fields = [
            'theme', 'first_name', 'last_name', 'phone_number', 'email',
            'text', 'images', 'uploaded_images', 'created_at'
        ]

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        feedback = Feedback.objects.create(**validated_data)

        for image in uploaded_images:
            FeedbackImage.objects.create(feedback=feedback, image=image)

        return feedback
