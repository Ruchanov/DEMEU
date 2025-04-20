from django.urls import path
from .views import NotificationListView, mark_as_read, mark_all_as_read, delete_all_notifications, \
    send_test_notification

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/mark-as-read/', mark_as_read, name='notification-mark-read'),
    path('mark-all-as-read/', mark_all_as_read, name='notifications-mark-all'),
    path('delete-all/', delete_all_notifications, name='notifications-delete-all'),
    path('send-test/', send_test_notification, name='send-test-notification'),
]
