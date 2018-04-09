from django.contrib import admin

# # Register your models here.
from . models import User, BoolParameter


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "room_id", "device_id", "pseudo", "consumption_good", "production_good", "tutorial_done")


class BoolParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "value")


admin.site.register(User, UserAdmin)
admin.site.register(BoolParameter, BoolParameterAdmin)

