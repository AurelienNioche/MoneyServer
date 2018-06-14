from django.db import transaction
from django.utils import timezone
import datetime
from channels.generic.websocket import JsonWebsocketConsumer, SyncConsumer, AsyncConsumer
from asgiref.sync import async_to_sync
from dashboard.models import ConnectedTablet, IntParameter
import threading
import subprocess

from utils import utils

from channels.layers import get_channel_layer


class DashboardWebSocketConsumer(JsonWebsocketConsumer):

    def connect(self):

        self.accept()

    def disconnect(self, close_code):

        utils.log(f'Disconnection! close code: {close_code}', f=self.disconnect)
        # self._group_discard('all')

    def receive_json(self, content, **kwargs):

        if 'register' in self.scope['path']:
            register_tablet(content['deviceId'], content['tabletNumber'])
            self.send('Done!')

    def group_message(self, message):

        """
        Send json to a group, called by self._group_send
        method and WSDialog.group_send from outside
        :param message:
        :return:
        """

        data = message['data']
        group = message['group']
        is_json = message['json']

        if is_json:
            try:
                utils.log(f'Sending to group {group}: {data}', f=self._group_send)
            except UnicodeEncodeError:
                print('Error printing request.')

            self.send_json(data)
        else:
            self.send(data)

    def _send_to_worker(self, demand, data):

        async_to_sync(self.channel_layer.send)(
            'receipt-consumer',
            {
                'type': 'generic',
                'demand': demand,
                'receipt_data': data
            },
        )

    def _group_send(self, group, data, json=True):

        """
        Send data to a desired group of users
        :param group:
        :param data:
        :return:
        """

        async_to_sync(self.channel_layer.group_send)(
            group,
            {
                'type': 'group.message',
                'data': data,
                'group': group,
                'json': json
             }
        )

    def _group_add(self, group):

        """
        add a user to a group
        :param group:
        """
        async_to_sync(self.channel_layer.group_add)(
            group,
            self.channel_name
        )

    def _group_discard(self, group):

        """
        remove a user from a group
        :param group:
        """
        async_to_sync(self.channel_layer.group_discard)(
            group,
            self.channel_name
        )


class WSDialog:

    @staticmethod
    def group_send(group, data, json=True):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group,
            {
                'type': 'group.message',
                'data': data,
                'group': group,
                'json': json
             }
        )

    @staticmethod
    def group_add(group):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_add)(
            group,
            channel_layer.channel_name
        )


def register_tablet(device_id, tablet_id):

    t = ConnectedTablet.objects.filter(device_id=device_id).first()

    if t:

        t.delete()

    t = ConnectedTablet(
        device_id=device_id,
        tablet_id=tablet_id,
        connected=False,
        time_last_request=timezone.now()
    )

    t.save()


def check_connected_users(devices):

    for d in devices:
        connected = not _is_disconnected(d.time_last_request)
        if connected != d.connected:
            d.connected = connected
            d.save(update_fields=["connected"])


def _is_disconnected(reference_time):

    # Then get the timezone
    tz_info = reference_time.tzinfo
    # Get time now using timezone info
    t_now = datetime.datetime.now(tz_info)

    param = IntParameter.objects.filter(name="disconnected_timeout").first()

    if param is None:

        param = IntParameter(name="disconnected_timeout", value=15)
        param.save()

    delta = datetime.timedelta(seconds=param.value)

    # If more than X seconds since the last request
    timeout = t_now > reference_time + delta

    return timeout


def _set_time_last_request(d):
    d.time_last_request = timezone.now()
    d.save(update_fields=["time_last_request"])






