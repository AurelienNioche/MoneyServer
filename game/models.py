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
    device_id = models.TextField(unique=True)
    pseudo = models.TextField(unique=True)
    age = models.IntegerField(null=True)
    gender = models.TextField(null=True)
    production_good = models.IntegerField()
    consumption_good = models.IntegerField()
    score = models.IntegerField(default=0)
    tutorial_done = models.NullBooleanField()
    tutorial_score = models.IntegerField()


class TutorialChoice(models.Model):
    room_id = models.IntegerField()
    user_id = models.IntegerField(null=True)
    good_in_hand = models.IntegerField(null=True)
    desired_good = models.IntegerField(null=True)
    t = models.IntegerField()
    success = models.NullBooleanField(null=True)


class Choice(models.Model):
    room_id = models.IntegerField()
    user_id = models.IntegerField(null=True)
    good_in_hand = models.IntegerField(null=True)
    desired_good = models.IntegerField(null=True)
    t = models.IntegerField()
    success = models.NullBooleanField(null=True)


class BoolParameter(models.Model):
    name = models.TextField(unique=True)
    value = models.BooleanField()
