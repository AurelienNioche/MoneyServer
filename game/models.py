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
    age = models.IntegerField(null=True)
    gender = models.IntegerField(null=True)
    tutorial_progression = models.IntegerField()
    production_good = models.IntegerField()
    consumption_good = models.IntegerField()
    score = models.IntegerField(default=0)


class Choice(models.Model):
    room_id = models.IntegerField()
    user_id = models.IntegerField(null=True)
    good_in_hand = models.IntegerField(null=True)
    desired_good = models.IntegerField(null=True)
    t = models.IntegerField()
    success = models.NullBooleanField(null=True)


class BoolParameter(models.Model):
    name = models.TextField()
    value = models.BooleanField()
