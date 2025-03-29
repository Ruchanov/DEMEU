from celery import shared_task
from .models import Publication
from django.utils import timezone


@shared_task
def check_publication_status():
    print("🕒 Циклическая задача запущена: проверка публикаций")

    now = timezone.now()
    publications = Publication.objects.filter(status='active')
    for pub in publications:
        donated = pub.total_donated()
        if donated >= pub.amount:
            pub.status = 'successful'
            pub.is_archived = True
            pub.save()
            print(f"[✓] {pub.title} marked as successful.")
        elif pub.expires_at and pub.expires_at <= now:
            pub.status = 'expired'
            pub.is_archived = True
            pub.save()
            print(f"[⌛] {pub.title} expired and archived.")
