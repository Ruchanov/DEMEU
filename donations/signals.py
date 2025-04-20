from django.db.models.signals import post_save
from django.dispatch import receiver
from donations.models import Donation
from publications.models import Publication
from notifications.utils import notify_user, notify_top_donor
from django.db.models import Sum

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


@receiver(post_save, sender=Donation)
def notify_new_donation(sender, instance, created, **kwargs):
    if not created:
        return

    publication = instance.publication
    author = publication.author
    donor = instance.donor

    # Уведомление автору
    if donor and author != donor:
        notify_user(
            user=author,
            verb="💰 Кто-то пожертвовал на вашу публикацию",
            target=f"{donor.first_name} отправил {instance.donor_amount} ₸",
            url=f"/post/{publication.id}"
        )

    # ✅ Уведомление донору, если он входит в топ-3
    if donor:
        top_donors = (
            publication.donations
            .values('donor')
            .annotate(total=Sum('donor_amount'))
            .order_by('-total')[:3]
        )
        if any(d['donor'] == donor.id for d in top_donors):
            notify_top_donor(donor, publication)

@receiver(post_save, sender=Donation)
def notify_half_goal_reached(sender, instance, created, **kwargs):
    if not created:
        return

    publication = instance.publication
    author = publication.author
    total_donated = publication.total_donated()
    goal = publication.amount

    if goal > 0 and 45 <= (total_donated / goal) * 100 < 55:
        notify_user(
            user=author,
            verb="🎯 Ваша публикация достигла 50% цели!",
            target=publication.title,
            url=f"/post/{publication.id}"
        )

@receiver(post_save, sender=Donation)
def notify_goal_reached(sender, instance, created, **kwargs):
    if not created:
        return

    publication = instance.publication
    author = publication.author
    total_donated = publication.total_donated()

    if total_donated >= publication.amount and publication.status != 'successful':
        notify_user(
            user=author,
            verb="🎉 Цель сбора достигнута!",
            target=publication.title,
            url=f"/post/{publication.id}"
        )