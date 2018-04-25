from game.models import User
from collections import Counter


def get_data(room_id):

    user_states = User.objects.values_list('state')

    values = [{"label": str(k[0]), "value": v} for k, v in Counter(user_states).items()]

    t = 0
    room_state = 'welcome'

    return t, room_state, values

