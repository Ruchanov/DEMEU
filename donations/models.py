from django.db import models
from django.utils import timezone
from django.conf import settings
from publications.models import Publication

class Donation(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='donations')
    donor_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        donor_name = "Anonymous"
        if self.donor:
            donor_name = f"{self.donor.first_name} {self.donor.last_name}".strip()
        return f"{donor_name} donated {self.donor_amount}"