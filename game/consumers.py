from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from game.room.state import demand_state_mapping

from channels.layers import get_channel_layer

import game.views


class WebSocketConsumer(JsonWebsocketConsumer):

    def connect(self):

        self.accept()

    def disconnect(self, close_code):

        for state in demand_state_mapping.keys():
            self._group_discard(group=state)

    def receive_json(self, content, **kwargs):

        to_reply = game.views.client_request(content)

        self.send_json(to_reply)
        print(f"\nSending: {to_reply}\n")

        # Add user to groups
        self._on_receive(to_reply)

    def _on_receive(self, content):

        user_id = content.get('userId')
        demand = content.get('demand')
        t = content.get('t')
        state = demand_state_mapping.get(demand)

        if user_id:

            self._group_add(group=f'user-{user_id}')

        if demand == 'choice':

            self._group_add(f'game-t-{t}')
            self._group_discard(f'game-t-{t-1}')

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
        print(f'\nSending to group {group}: {data}\n')
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


class WSDialog:

    @staticmethod
    def group_send(group, data):

        channel_layer = get_channel_layer()

        print(f'\nSending to group {group}: {data}\n')

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






