from django.contrib import admin

# # Register your models here.
from . models import User, BoolParameter, Choice, TutorialChoice, Room, Receipt, ConsumerState


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id", "room_id", "device_id", "pseudo", "consumption_good",
        "production_good",
        "training_done",
         "gender", "age", "state", 'score',
        'training_score',
        'player_id'
    )


class BoolParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "value")


class ChoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'good_in_hand', 'desired_good', 'user_id', 'player_id', 'room_id', 'success', 't',
    )


class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'n_user', 'opened',
          't', 'training_t',
        't_max', 'training_t_max',
        "state", "n_type", "types"
    )


class TutorialChoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'desired_good', 'good_in_hand', 'user_id', 'player_id','room_id', 'success', 't'
    )


class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'player_id', 'received', 'demand', 't')


class ConsumerStateAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'init', 'survey', 'training_choice', 'training_done', 'choice', 'treating_t')


admin.site.register(User, UserAdmin)
admin.site.register(BoolParameter, BoolParameterAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(TutorialChoice, TutorialChoiceAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(ConsumerState, ConsumerStateAdmin)

