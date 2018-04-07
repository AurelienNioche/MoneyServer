from django.conf.urls import include, url
from django.contrib import admin

from django.views.generic.base import RedirectView


app_name = "adminbase"
urlpatterns = [
    url(r'^', include('dashboard.urls', namespace='dashboard')),
    url(r'^', include('game.urls', namespace='game')),
    url(r'^admin/', admin.site.urls),
    url(r'^index/', RedirectView.as_view(url='/room_management'))
]
