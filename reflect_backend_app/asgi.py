import os
import django
from channels.routing import get_default_application
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reflect_backend_app.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from api.ai.consumers import NotificationConsumer  # или другой путь

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # Укажи свой путь WebSocket
            path("ws/notifications/", NotificationConsumer.as_asgi()),
        ])
    ),
})
