from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from .serializers import NotificationSerializer

def notify_user(user, verb, target=None, url=None):
    notification = Notification.objects.create(
        recipient=user,
        verb=verb,
        target=target,
        url=url
    )
    channel_layer = get_channel_layer()
    group_name = f"user_{user.id}"
    serializer = NotificationSerializer(notification)

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "content": serializer.data
        }
    )
def notify_top_donor(user, publication):
    notify_user(
        user=user,
        verb="🏆 Вы вошли в топ-донатёры публикации",
        target=publication.title,
        url=f"/post/{publication.id}"
    )


