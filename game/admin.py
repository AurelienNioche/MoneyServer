from django.contrib import admin

# # Register your models here.
from . models import User, BoolParameter, Choice, TutorialChoice, Room


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "room_id", "device_id", "pseudo", "consumption_good",
        "production_good", "tutorial_done", "gender", "age", "state", 'score',
        'tutorial_score'
    )


class BoolParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "value")


class ChoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'desired_good', 'good_in_hand', 'user_id', 'room_id', 'success', 't'
    )


class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'x0', 'x1', 'x2', 'n_user', 'opened', 't', 'tutorial_t', 't_max', 'tutorial_t_max', "state"
    )


class TutorialChoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'desired_good', 'good_in_hand', 'user_id', 'room_id', 'success', 't'
    )


admin.site.register(User, UserAdmin)
admin.site.register(BoolParameter, BoolParameterAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(TutorialChoice, TutorialChoiceAdmin)
admin.site.register(Room, RoomAdmin)


