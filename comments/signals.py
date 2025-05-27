from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
from notifications.utils import notify_user

@receiver(post_save, sender=Comment)
def notify_new_comment(sender, instance, created, **kwargs):
    if created:
        publication = instance.publication
        author = publication.author
        commenter = instance.author

        if author != commenter:
            notify_user(
                user=author,
                verb="💬 Новый комментарий к вашей публикации",
                target=f"{commenter.first_name}: {instance.content[:30]}...",
                url=f"http://localhost:8000/publications/{publication.id}/"
            )
