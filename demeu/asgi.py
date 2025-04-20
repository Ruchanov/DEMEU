"""
ASGI config for demeu project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from notifications.routing import websocket_urlpatterns
from notifications.middleware import JWTAuthMiddleware
from django.core.asgi import get_asgi_application
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demeu.settings")
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
