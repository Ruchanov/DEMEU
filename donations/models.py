from django.db import models
from django.utils import timezone
from django.conf import settings
from publications.models import Publication

class Donation(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='donations')
    donor_amount = models.DecimalField(max_digits=10, decimal_places=2)
    support_percentage = models.PositiveIntegerField(default=0)
    support_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Автоматически рассчитывает поддержку и общий платеж перед сохранением
        self.support_amount = (self.donor_amount * self.support_percentage) / 100
        self.total_amount = self.donor_amount + self.support_amount
        super().save(*args, **kwargs)

    def __str__(self):
        donor_name = f"{self.donor.first_name} {self.donor.last_name}" if self.donor else "Anonymous"
        return f"{donor_name} donated {self.total_amount} ₸"