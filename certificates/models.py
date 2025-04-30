from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CertificateLevel(models.TextChoices):
    BRONZE = 'bronze', 'Bronze'
    SILVER = 'silver', 'Silver'
    GOLD = 'gold', 'Gold'

class UserCertificate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='certificate')
    level = models.CharField(max_length=10, choices=CertificateLevel.choices)
    pdf = models.FileField(upload_to='certificates/', null=True, blank=True)
    achieved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.level.capitalize()}"
