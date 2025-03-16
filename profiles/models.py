import os
from io import BytesIO
from datetime import date
from PIL import Image

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile


def validate_image_size(image):
    max_size_mb = 5
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Image size should not exceed {max_size_mb}MB.")


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    instagram = models.URLField(max_length=255, blank=True, null=True)
    whatsapp = models.URLField(max_length=255, blank=True, null=True)
    facebook = models.URLField(max_length=255, blank=True, null=True)
    telegram = models.URLField(max_length=255, blank=True, null=True)

    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, validators=[validate_image_size])

    def save(self, *args, **kwargs):
        if self.pk:
            old_avatar = Profile.objects.get(pk=self.pk).avatar
            if old_avatar and old_avatar != self.avatar and old_avatar.path:
                if os.path.exists(old_avatar.path):
                    os.remove(old_avatar.path)

        if self.avatar:
            self.avatar = self.convert_to_webp(self.avatar)

        super().save(*args, **kwargs)

    def convert_to_webp(self, image, size=(300, 300)):
        img = Image.open(image)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        img.thumbnail(size, Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=85)

        return ContentFile(buffer.getvalue(), name=f"{os.path.splitext(image.name)[0]}.webp")

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                        (today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def __str__(self):
        return f"{self.user.email}'s Profile"

class ProfileView(models.Model):
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE, related_name="views")
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'viewer')

    def __str__(self):
        return f"{self.viewer.email} viewed {self.profile.user.email}'s profile"