from django.db import models


class Room(models.Model):
    x0 = models.IntegerField()
    x1 = models.IntegerField()
    x2 = models.IntegerField()
    n_user = models.IntegerField()
    t = models.IntegerField()
    ending_t = models.IntegerField()
    trial = models.BooleanField(default=False)
    opened = models.BooleanField(default=True)
    state = models.TextField()


class User(models.Model):
    room_id = models.IntegerField()
    device_id = models.TextField()
    pseudo = models.TextField()
    state = models.IntegerField()
    age = models.IntegerField()
    gender = models.IntegerField()
    tutorial_progression = models.IntegerField()
    production_good = models.IntegerField()
    consumption_good = models.IntegerField()


class Choice(models.Model):
    room_id = models.IntegerField()
    user_id = models.IntegerField(null=True)
    good_in_hand = models.IntegerField(null=True)
    desired_good = models.IntegerField(null=True)
    t = models.IntegerField()


class IntParameter(models.Model):
    name = models.TextField()
    value = models.IntegerField()
