from django.db import models
from django.conf import settings
from publications.models import Publication

class FavoritePublication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_publications')
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'publication')

    def __str__(self):
        return f"User {self.user} favorited publication {self.publication.title}"


class FavoriteUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_users')
    favorite_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followers')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User {self.user} follows {self.favorite_user}"
