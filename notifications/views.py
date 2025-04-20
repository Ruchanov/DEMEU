from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Notification
from .serializers import NotificationSerializer
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .utils import notify_user

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user).order_by('-created_at')

        if self.request.query_params.get('unread') == 'true':
            queryset = queryset.filter(is_read=False)

        return queryset


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_as_read(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_as_read(request):
    request.user.notifications.update(is_read=True)
    return Response({'status': 'all marked as read'})


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_all_notifications(request):
    request.user.notifications.all().delete()
    return Response({'status': 'all deleted'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Временно, чтобы можно было тестировать
def send_test_notification(request):
    user_id = request.data.get("user_id")
    verb = request.data.get("verb", "Test Notification")
    target = request.data.get("target", "Example target")
    url = request.data.get("url", "http://example.com")

    try:
        user = get_user_model().objects.get(id=user_id)
        notify_user(user, verb=verb, target=target, url=url)
        return JsonResponse({"status": "sent", "user_id": user.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
