from django.urls import path
from .views import ProfileDetailView, ProfilePublicView, ProfileSearchView

urlpatterns = [
    path('me/', ProfileDetailView.as_view(), name='profile-detail'),
    path('<int:user_id>/', ProfilePublicView.as_view(), name='profile-public'),
    path('search/', ProfileSearchView.as_view(), name='profile-search'),  # Поиск пользователей
]