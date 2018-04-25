from django.db import models


class Room(models.Model):
    n_user = models.IntegerField(default=None, null=True)
    n_type = models.IntegerField(default=None, null=True)
    types = models.TextField(default=None, null=True)
    t = models.IntegerField(default=None, null=True)
    t_max = models.IntegerField(default=None, null=True)
    tutorial_t = models.IntegerField(default=None, null=True)
    tutorial_t_max = models.IntegerField(default=None, null=True)
    trial = models.BooleanField(default=False)
    opened = models.BooleanField(default=True, unique=True)
    state = models.TextField(default=None, null=True)


class User(models.Model):
    room_id = models.IntegerField(default=None, null=True)
    device_id = models.TextField(default=None, null=True)
    player_id = models.IntegerField(default=None, null=True)
    pseudo = models.TextField(default=None, null=True)
    age = models.IntegerField(default=None, null=True)
    gender = models.TextField(default=None, null=True)
    production_good = models.IntegerField(default=None, null=True)
    consumption_good = models.IntegerField(default=None, null=True)
    score = models.IntegerField(default=0)
    tutorial_done = models.NullBooleanField(default=None, null=True)
    tutorial_score = models.IntegerField(default=None, null=True)
    state = models.TextField(default=None, null=True)

    class Meta:
        unique_together = [
            ('room_id', 'device_id'),
            ('room_id', 'player_id'),
            ('room_id', 'pseudo')
        ]


class TutorialChoice(models.Model):
    room_id = models.IntegerField(default=None, null=True)
    player_id = models.IntegerField(default=None, null=True)
    t = models.IntegerField(default=None, null=True)
    user_id = models.IntegerField(default=None, null=True)
    good_in_hand = models.IntegerField(default=None, null=True)
    desired_good = models.IntegerField(default=None, null=True)
    success = models.NullBooleanField(default=None, null=True)


class Choice(models.Model):
    room_id = models.IntegerField(default=None, null=True)
    player_id = models.IntegerField(default=None, null=True)
    t = models.IntegerField(default=None, null=True)
    user_id = models.IntegerField(default=None, null=True)
    good_in_hand = models.IntegerField(default=None, null=True)
    desired_good = models.IntegerField(default=None, null=True)
    success = models.NullBooleanField(default=None, null=True)

    class Meta:
        unique_together = [
            ('user_id', 't'),
        ]


class BoolParameter(models.Model):
    name = models.TextField(default=None, null=True)
    value = models.NullBooleanField(default=None, null=True)


