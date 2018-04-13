from django.db import models


class Room(models.Model):
    x0 = models.IntegerField()
    x1 = models.IntegerField()
    x2 = models.IntegerField()
    n_user = models.IntegerField()
    t = models.IntegerField()
    t_max = models.IntegerField()
    tutorial_t = models.IntegerField()
    tutorial_t_max = models.IntegerField()
    trial = models.BooleanField(default=False)
    opened = models.BooleanField(default=True)
    state = models.TextField()


class User(models.Model):
    room_id = models.IntegerField()
    device_id = models.TextField()
    player_id = models.IntegerField()
    pseudo = models.TextField()
    age = models.IntegerField(null=True)
    gender = models.TextField(null=True)
    production_good = models.IntegerField(null=True)
    consumption_good = models.IntegerField(null=True)
    score = models.IntegerField(default=0)
    tutorial_done = models.NullBooleanField()
    tutorial_score = models.IntegerField()
    state = models.TextField(null=True)

    class Meta:
        unique_together = [
            ('room_id', 'device_id'),
            ('room_id', 'player_id'),
            ('room_id', 'pseudo')
        ]


class Type(models.Model):
    room_id = models.IntegerField()
    player_id = models.IntegerField()
    user_id = models.IntegerField(null=True)
    production_good = models.IntegerField()


class TutorialChoice(models.Model):
    room_id = models.IntegerField()
    player_id = models.IntegerField()
    t = models.IntegerField()
    user_id = models.IntegerField(null=True)
    good_in_hand = models.IntegerField(null=True)
    desired_good = models.IntegerField(null=True)
    final_good = models.IntegerField(null=True)
    success = models.NullBooleanField(null=True)


class Choice(models.Model):
    room_id = models.IntegerField()
    player_id = models.IntegerField()
    t = models.IntegerField()
    user_id = models.IntegerField(null=True)
    good_in_hand = models.IntegerField(null=True)
    desired_good = models.IntegerField(null=True)
    success = models.NullBooleanField(null=True)

    class Meta:
        unique_together = [
            ('user_id', 't'),
        ]


class BoolParameter(models.Model):
    name = models.TextField(unique=True)
    value = models.BooleanField()


