import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prochat.settings')

django_asgi_app = get_asgi_application()

from chat.routing import websocket_urlpatterns as chat_ws
from meetings.routing import websocket_urlpatterns as meetings_ws
from notifications.routing import websocket_urlpatterns as notifications_ws
from whiteboard.routing import websocket_urlpatterns as whiteboard_ws
from ai.routing import websocket_urlpatterns as ai_ws
from tasks.routing import websocket_urlpatterns as tasks_ws

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat_ws +
            meetings_ws +
            notifications_ws +
            whiteboard_ws +
            ai_ws +
            tasks_ws
        )
    ),
})