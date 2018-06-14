from django.contrib import admin

# Register your models here.
from . models import IntParameter, ConnectedTablet


class IntParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "unit")


class ConnectedTabletAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'tablet_id', 'connected', 'time_last_request')


admin.site.register(IntParameter, IntParameterAdmin)
admin.site.register(ConnectedTablet, ConnectedTabletAdmin)
