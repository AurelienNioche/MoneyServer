from django.urls import path
from django.conf.urls import url

from . import consumers


websocket_urlpatterns = [
    path('ws', consumers.WebSocketConsumer),
    url(r'^ws/$', consumers.WebSocketConsumer)
]