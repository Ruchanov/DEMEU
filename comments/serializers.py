from rest_framework import serializers
from .models import Comment
from publications.models import Publication
from profiles.models import Profile


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    author_id = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author','author_id','avatar', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'publication', 'created_at', 'updated_at']

    def create(self, validated_data):
        publication_id = self.context['publication_id']
        publication = Publication.objects.get(id=publication_id)

        comment = Comment.objects.create(publication=publication, **validated_data)
        return comment

    def get_avatar(self, obj):
        if obj.author.profile.avatar:
            request = self.context.get('request')
            avatar_url = obj.author.profile.avatar.url
            return request.build_absolute_uri(avatar_url) if request else avatar_url
        return None

    def get_author_id(self, obj):
        return obj.author.id if obj.author else None
