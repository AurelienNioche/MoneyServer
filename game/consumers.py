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

    def receive_json(self, content, **kwargs):

        to_reply, consumer_info = game.views.client_request(content)

        if to_reply and consumer_info:

            self._group_management(consumer_info)

            self.send_json(to_reply)

            try:
                utils.log(f'Sending to current channel: {to_reply}', f=self.receive_json)
            except UnicodeEncodeError:
                print('Error printing request.')

            cond0 = not to_reply['wait']

            cond1 = game.consumer.state.is_consumer_already_treating_demand(
                demand=consumer_info['demand'],
                room_id=consumer_info['room_id'],
                t=consumer_info.get('t'),
            )

            if cond0 and not cond1:

                self._send_to_worker(demand=consumer_info['demand'], data=consumer_info)

    def _send_to_worker(self, demand, data):

        async_to_sync(self.channel_layer.send)(
            'receipt-consumer',
            {
                'type': 'generic',
                'demand': demand,
                'receipt_data': data
            },
        )

    def _group_management(self, consumer_info):

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
        Send json to a group, called by self._group_send
        method and WSDialog.group_send from outside
        :param message:
        :return:
        """

        data = message['data']
        group = message['group']

        try:
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

        utils.log(f'ReceiptConsumer begins the task {demand}', f=self.generic)

        game.consumer.state.treat_demand(demand=demand, room_id=kwargs['room_id'], t=kwargs.get('t'))

        func = getattr(game.receipt_views, demand)
        func(kwargs)

        game.consumer.state.finished_treating_demand(demand=demand, room_id=kwargs['room_id'], t=kwargs.get('t'))

        utils.log(f'ReceiptConsumer finished to treat the task {demand}', f=self.generic)


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





