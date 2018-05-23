from channels.generic.websocket import JsonWebsocketConsumer, SyncConsumer
from asgiref.sync import async_to_sync
from game.room.state import demand_state_mapping

from channels.layers import get_channel_layer

import game.views
import game.receipt_views


class WebSocketConsumer(JsonWebsocketConsumer):

    def connect(self):

        self.accept()

    def disconnect(self, close_code):

        pass
        # for state in demand_state_mapping.keys():
        #     self._group_discard(group=state)

    def receive_json(self, content, **kwargs):

        if content['demand'] != 'receipt_confirmation':

            to_reply, group_reply = game.views.client_request(content)

            self.send_json(to_reply)

            try:
                print(f"\nSending: {to_reply}\n")
            except UnicodeEncodeError:
                print('Error printing request.')

            self._group_management(to_reply)

            if not to_reply['wait']:

                self._send_to_worker(demand=to_reply['demand'], data=group_reply)

        else:

            game.views.client_request(content)

    def _send_to_worker(self, demand, data):

        async_to_sync(self.channel_layer.send)(
            'receipt-consumer',
            {
                'type': 'generic',
                'data': {'demand': demand, 'receipt_data': data}
            },
        )

    def _group_management(self, to_reply):

        user_id = to_reply.get('userId')

        demand = to_reply.get('demand')
        demand_func = getattr(game.views, demand) if isinstance(demand, str) else None

        state = demand_state_mapping.get(demand)

        if user_id:
            self._group_add(group=f'user-{user_id}')

        if demand_func == game.views.choice:
            t = to_reply.get('t')
            self._group_add(f'game-t-{t}')
            self._group_discard(f'game-t-{t-1}')
            self._group_discard('training-done')

        if demand_func == game.views.training_done:
            self._group_add('training-done')

        # Remove user from all other groups
        for group in demand_state_mapping.keys():
            self._group_discard(group=group)

        self._group_add(group=state)

    def _group_send(self, group, data):

        """
        Send data to a desired group of users
        :param group:
        :param data:
        :return:
        """

        try:
            print(f'\nSending to group {group}: {data}\n')
        except UnicodeEncodeError:
            print('Error printing request.')

        async_to_sync(self.channel_layer.group_send)(
            group,
            {'type': 'group.message', 'text': data}
        )

    def group_message(self, data):
        """
        Send json to a group, called by group_send
        method.
        :param data:
        :return:
        """

        self.send_json(data['text'])

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

        demand = message['data']['demand']
        kwargs = message['data']['receipt_data']

        func = getattr(game.receipt_views, demand)
        func(kwargs)


class WSDialog:

    @staticmethod
    def group_send(group, data):

        channel_layer = get_channel_layer()

        try:
            print(f'\nSending to group {group}: {data}\n')
        except UnicodeEncodeError:
            print('Error printing request.')

        async_to_sync(channel_layer.group_send)(
            group,
            {'type': 'group.message', 'text': data}
        )

    @staticmethod
    def group_add(group):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_add)(
            group,
            channel_layer.channel_name
        )





