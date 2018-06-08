from django.db import transaction
from channels.generic.websocket import JsonWebsocketConsumer, SyncConsumer, AsyncConsumer
from asgiref.sync import async_to_sync
import threading

from utils import utils

from game.room.state import demand_state_mapping

from channels.layers import get_channel_layer

import game.views
import game.receipt_views
import game.consumer.state
import game.room.client
import game.params.client


class WebSocketConsumer(JsonWebsocketConsumer):

    def connect(self):

        self.accept()

        # self.send_json(
        #     content=game.params.client.get_request_parameters()
        # )

        # self._group_add('all')
        # self.start_pinging()

    def disconnect(self, close_code):

        utils.log(f'Disconnection! close code: {close_code}', f=self.disconnect)
        # self._group_discard('all')

    def receive(self, **kwargs):

        if kwargs['text_data'] == 'ping':
            #utils.log('I received a ping, I will send a pong', f=self.receive)
            self.send('pong')

        else:
            super().receive(**kwargs)

    def receive_json(self, content, **kwargs):

        to_reply, consumer_info = game.views.client_request(content)

        if to_reply and consumer_info:

            self._group_management(consumer_info)

            self.send_json(to_reply)

            try:
                utils.log(f'Sending to current channel: {to_reply}', f=self.receive_json)
            except UnicodeEncodeError:
                print('Error printing request.')

            # If clients do not need to wait
            # and are waiting for answer
            if not to_reply['wait']:

                self._worker_management(consumer_info)

    def _worker_management(self, consumer_info):

        task_done = game.consumer.state.task_is_done(
            demand=consumer_info['demand'],
            room_id=consumer_info['room_id'],
            t=consumer_info.get('t'),
        )

        utils.log(
            f'Verifying that worker did the task {consumer_info["demand"]}',
            f=self._worker_management
        )

        if not task_done and task_done is not None:

            self._send_to_worker(
                demand=consumer_info['demand'], data=consumer_info
            )

        else:

            utils.log(
                f'Worker already did task {consumer_info["demand"]}, t={consumer_info.get("t")}',
                f=self._worker_management
            )

    def _group_management(self, consumer_info):

        """
        Adding current connected user to group
        :param consumer_info:
        :return:
        """

        user_id = consumer_info.get('user_id')
        demand = consumer_info.get('demand')

        demand_func = \
            getattr(game.views, demand) if isinstance(demand, str) else None

        state = demand_state_mapping.get(demand)

        if user_id:

            # if user_id is available
            # add the corresponding group
            # Each user_id group matches only
            # user/client/device
            id_group = f'user-{user_id}'
            utils.log(f'Adding group {id_group}', f=self._group_management)
            self._group_add(group=id_group)

        if demand_func == game.views.choice:

            t = consumer_info.get('t')

            # Add user to the current t group
            game_group_t = f'game-t-{t}'
            self._group_add(game_group_t)

            # Discard user from group t - 1
            game_group_t_minus_1 = f'game-t-{t-1}'
            self._group_discard(game_group_t_minus_1)

            # If user calls the choice method it means that
            # training is done
            # So that we remove him from that
            # group too
            training_group_discard = 'training-done'
            self._group_discard(training_group_discard)

        elif demand_func == game.views.training_done:

            # If training_done is called add user to the
            # corresponding group
            training_group_add = 'training-done'
            self._group_add(training_group_add)

        # Remove user from all other groups
        for group in demand_state_mapping.keys():
            self._group_discard(group=group)

        if state:
            self._group_add(group=state)

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

    def start_pinging(self):

        async_to_sync(self.channel_layer.send)(
            'ping-consumer',
            {
                'type': 'ping'
            },
        )

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


class ReceiptConsumer(SyncConsumer):
    def generic(self, message):

        demand = message['demand']
        kwargs = message['receipt_data']

        utils.log(f'ReceiptConsumer begins the task {demand}', f=self.generic)

        with transaction.atomic():

            if demand != 'training_choice':
                task = game.consumer.state.treat_demand(demand=demand, room_id=kwargs['room_id'], t=kwargs.get('t'))

            func = getattr(game.receipt_views, demand)
            func(kwargs)

            if demand != 'training_choice':
                game.consumer.state.finished_treating_demand(task=task)

        utils.log(f'ReceiptConsumer finished to treat the task {demand}', f=self.generic)


class PingConsumer(SyncConsumer):

    def ping(self, *args):

        utils.log('Start pinging', f=self.ping)

        while True:

            WSDialog.group_send(group='all', data='ping', json=False)

            frequency = game.params.client.get_ping_frequency()

            threading.Event().wait(frequency)


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





