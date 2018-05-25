from channels.generic.websocket import JsonWebsocketConsumer, SyncConsumer
from asgiref.sync import async_to_sync

from utils import utils

from game.room.state import demand_state_mapping

from channels.layers import get_channel_layer

import game.views
import game.receipt_views
import game.consumer.state


class WebSocketConsumer(JsonWebsocketConsumer):

    def connect(self):

        self.accept()

    def disconnect(self, close_code):

        pass
        # for state in demand_state_mapping.keys():
        #     self._group_discard(group=state)

    def receive_json(self, content, **kwargs):

        to_reply, consumer_info = game.views.client_request(content)

        if to_reply:

            self.send_json(to_reply)

            try:
                utils.log(f'Sending to current channel: {to_reply}', f=self.receive_json)
            except UnicodeEncodeError:
                print('Error printing request.')

            self._group_management(to_reply)

            cond0 = not to_reply['wait']
            cond1 = game.consumer.state.is_consumer_already_treating_demand(
                demand=consumer_info['demand'],
                room_id=consumer_info['room_id']
            )

            if cond0 and not cond1:
                print('Worker is not occupied')
                self._send_to_worker(demand=consumer_info['demand'], data=consumer_info)
            else:

                if cond1:
                    print('WORKER IS OCCUPIED')

    def _send_to_worker(self, demand, data):

        async_to_sync(self.channel_layer.send)(
            'receipt-consumer',
            {
                'type': 'generic',
                'demand': demand,
                'receipt_data': data
            },
        )

    def _group_management(self, to_reply):

        user_id = to_reply.get('userId')

        demand = to_reply.get('demand')
        demand_func = \
            getattr(game.views, demand) if isinstance(demand, str) else None

        state = demand_state_mapping.get(demand)

        if user_id:
            self._group_add(group=f'user-{user_id}')

        if demand_func == game.views.choice:
            t = to_reply.get('t')
            self._group_add(f'game-t-{t}')
            self._group_discard(f'game-t-{t-1}')
            self._group_discard('training-done')

        elif demand_func == game.views.training_done:
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

        async_to_sync(self.channel_layer.group_send)(
            group,
            {
                'type': 'group.message',
                'data': data,
                'group': group
             }
        )

    def group_message(self, message):
        """
        Send json to a group, called by group_send
        method.
        :param message:
        :return:
        """

        data = message['data']
        group = message['group']

        if data.get('receipt_views'):
            raise Exception

        try:
            print(f'Sending to group {group}')
            utils.log(f'Sending to group {group}: {data}', f=self._group_send)
        except UnicodeEncodeError:
            print('Error printing request.')

        self.send_json(data)

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

        print('Task Launched')

        game.consumer.state.treat_demand(demand=demand, room_id=kwargs['room_id'])

        func = getattr(game.receipt_views, demand)
        func(kwargs)

        print('Task end')

        game.consumer.state.finished_treating_demand(demand=demand, room_id=kwargs['room_id'])


class WSDialog:

    @staticmethod
    def group_send(group, data):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            group,
            {
                'type': 'group.message',
                'data': data,
                'group': group,
             }
        )

    @staticmethod
    def group_add(group):

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_add)(
            group,
            channel_layer.channel_name
        )





