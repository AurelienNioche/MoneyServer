from django.urls import path
from django.conf.urls import url

from dashboard import consumers


websocket_urlpatterns = [
    path('ws/register', consumers.DashboardWebSocketConsumer),
    url(r'^ws/register/$', consumers.DashboardWebSocketConsumer),
]
