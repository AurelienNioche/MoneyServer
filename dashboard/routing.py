from django.urls import path
from django.conf.urls import url

from dashboard import consumers


websocket_urlpatterns = [
    path('ws/register', consumers.DashboardWebSocketConsumer),
    url(r'^ws/identity/$', consumers.DashboardWebSocketConsumer),
    url(r'^ws/connection/$', consumers.DashboardWebSocketConsumer),
    url(r'^ws/check_network/$', consumers.DashboardWebSocketConsumer),
]
