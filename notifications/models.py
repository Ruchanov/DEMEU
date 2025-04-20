from django.db import models
from django.conf import settings

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='notifications')
    verb = models.CharField(max_length=255)  # Например: "sent you a message", "donated to your post"
    target = models.CharField(max_length=255, null=True, blank=True)  # Например: "Publication: XYZ"
    url = models.URLField(null=True, blank=True)  # ссылка на объект (пост, профиль и т.д.)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.email} - {self.verb}"
