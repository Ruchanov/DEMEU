from celery import shared_task
from .models import Publication
from django.utils import timezone
from datetime import timedelta


@shared_task
def check_publication_status():
    print("🕒 Циклическая задача запущена: проверка публикаций")

    now = timezone.now()
    three_months_ago = now - timedelta(days=90)
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

    # Удаляем публикации, которые были архивированы более 3 месяцев назад
    old_archived = Publication.objects.filter(is_archived=True, updated_at__lte=three_months_ago)
    count = old_archived.count()
    old_archived.delete()
    if count:
        print(f"[🗑] Удалено {count} архивных публикаций старше 3 месяцев.")
