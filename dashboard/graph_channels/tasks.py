from channels import Group
import dashboard.graph_channels.helpers
from game.room.state import states
import time
import json


def update_graph(kwargs):

    room_id = kwargs['room_id']

    t_set = set()
    delay = 1
    user_states = []

    while True:

        t, room_state, data = dashboard.graph_channels.helpers.get_data(room_id=room_id)

        if room_state == states.game:

            if t not in t_set:

                t_set.add(t)

                Group('test').send({'data': data})

        elif user_states != data:

            user_states = data.copy()

            Group('test').send({
                'text': json.dumps(data),
            }, immediately=True)

        # if t == data['t_max']:
        #     break

        time.sleep(delay)

