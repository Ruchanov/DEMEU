from django.urls import path
from .views import GoogleLoginAPIView

urlpatterns = [
    path('login/', GoogleLoginAPIView.as_view(), name='google_login'),
]
