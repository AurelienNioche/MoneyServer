from django.db import models


class IntParameter(models.Model):

    name = models.TextField()
    value = models.IntegerField()
    unit = models.TextField()


class ConnectedTablet(models.Model):
    device_id = models.TextField()
    tablet_id = models.IntegerField()
    connected = models.BooleanField()
    time_last_request = models.DateTimeField(auto_now_add=True, blank=True)