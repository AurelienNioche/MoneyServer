from django.db import models


class Room(models.Model):
    pass


class User(models.Model):
    pass


class Choice(models.Model):
    pass


class IntParameter(models.Model):
    name = models.TextField()
    value = models.IntegerField()
