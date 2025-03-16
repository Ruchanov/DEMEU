import os

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, filters
from rest_framework.exceptions import NotFound
from accounts.models import User
from .models import Profile, ProfileView
from .serializers import ProfileSerializer
from accounts.serializers import UserSerializer


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if not hasattr(user, 'profile'):
            raise NotFound("User profile does not exist")
        return user.profile

    def perform_update(self, serializer):
        profile = self.get_object()
        old_avatar = profile.avatar

        serializer.save()

        if old_avatar and old_avatar != profile.avatar:
            if old_avatar.path and os.path.exists(old_avatar.path):
                old_avatar.delete(save=False)


class ProfilePublicView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        profile = get_object_or_404(Profile, user__id=user_id)

        # Фиксируем просмотр профиля
        viewer = self.request.user if self.request.user.is_authenticated else None
        if viewer and viewer != profile.user:
            ProfileView.objects.get_or_create(profile=profile, viewer=viewer)

        return profile


class ProfileSearchView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]  # Можно изменить на IsAuthenticated
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']

