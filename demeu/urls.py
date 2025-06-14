"""demeu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from donations.stripe_webhooks import stripe_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('profiles/', include('profiles.urls')),
    path('publications/', include('publications.urls')),
    path('donations/', include('donations.urls')),
    path('comments/', include('comments.urls')),
    path('favorites/', include('favorites.urls')),
    path('info/', include('info.urls')),
    path('auth/google/', include('google_auth.urls')),
    path('notifications/', include('notifications.urls')),
    path('certificates/', include('certificates.urls')),
    path('api/stripe/webhook/', stripe_webhook),
]

# Добавляем маршруты для обработки медиафайлов (например, аватары)
if settings.DEBUG:  # Только для отладки. В продакшене используем Nginx или другой сервер для медиа.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)