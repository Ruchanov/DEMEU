from django.db.models.signals import post_save
from django.dispatch import receiver
from donations.models import Donation
from publications.models import Publication

@receiver(post_save, sender=Donation)
def check_publication_funding(sender, instance, created, **kwargs):
    if not created:
        return

    publication = instance.publication
    total = publication.total_donated()

    if total >= publication.amount and publication.status != 'successful':
        publication.status = 'successful'
        publication.is_archived = True
        publication.save()
        print(f"✅ Публикация '{publication.title}' успешно завершена и отправлена в архив.")
