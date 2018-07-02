from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
import threading

from utils import utils

import game.params.client
import dashboard.tablets.client


class AbstractWebsocketConsumer(JsonWebsocketConsumer):

    def connect(self):

        self.accept()

    def disconnect(self, close_code):

        utils.log(f'Disconnection! close code: {close_code}', f=self.disconnect)
        # self._group_discard('all')

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
                if len(str(data)) < 100:
                    utils.log(f'Sending to group {group}: {data}', f=self._group_send)
            except UnicodeEncodeError:
                print('Error printing request.')

            self.send_json(data)

        else:
            self.send(data)

    def _send_to_worker(self, worker, demand, data):

        async_to_sync(self.channel_layer.send)(
            worker,
            {
                'type': demand,
                'data': data
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


class DashboardWebSocketConsumer(AbstractWebsocketConsumer):

    def receive_json(self, content, **kwargs):

        if 'identity' in self.scope['path']:

            dashboard.tablets.client.register_tablet(
                device_id=content['deviceId'],
                tablet_id=content['tabletNumber']
            )

            self.send('Done!')

        elif 'check_network' in self.scope['path']:

            self.send_json(
                game.params.client.get_request_parameters()
            )

        elif 'connection' in self.scope['path']:

            self._group_add('connection')

            self._send_to_worker(
                worker='connection-consumer', demand='check.connection', data=None
            )


class ConnectionConsumer(AbstractWebsocketConsumer):

    # Delay in seconds
    delay = 2

    def check_connection(self, message):

        while True:

            threading.Event().wait(self.delay)

            connection_table = dashboard.tablets.client.get_connection_table()

            self._group_send(
                group='connection',
                data={'html': connection_table}
            )
