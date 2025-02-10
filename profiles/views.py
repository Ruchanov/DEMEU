import os
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound

from .models import Profile
from .serializers import ProfileSerializer


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