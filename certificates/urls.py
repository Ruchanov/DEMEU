from django.urls import path
from .views import my_certificate_view, certificate_public_view

urlpatterns = [
    path('me/', my_certificate_view, name='my-certificate'),
    path('<int:user_id>/', certificate_public_view, name='public-certificate'),
]
