import os
from django.core.asgi import get_asgi_application
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from strangerChat.connections import Connection


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "strangerChat.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                 re_path(r'socket/(?P<chat_id>\w+)/$', Connection.as_asgi())
            ]
        ),
    ),
})