from game.models import Choice, TutorialChoice
from collections import namedtuple

from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

# Global states
States = namedtuple(
    'States',
    ['welcome', 'survey', 'tutorial', 'game', 'end']
)

states = States(
    welcome='welcome',
    survey='survey',
    tutorial='tutorial',
    game='game',
    end='end'
)


demand_state_mapping = {
    'init': states.welcome,
    'survey': states.survey,
    'tutorial': states.tutorial,
    'tutorial_choice': states.tutorial,
    'tutorial_done': states.tutorial,
    'choice': states.game
}


def get_progress_for_choices(rm, t, tuto=False):

    table = TutorialChoice if tuto else Choice
    n_choices = table.objects.filter(room_id=rm.id, t=t).exclude(desired_good=None).count()

    return round(n_choices / rm.n_user * 100)


def next_state(rm, state):

    rm.state = state

    # If room's state is end
    # definitely close the room
    if state == states.end:
        rm.opened = False

    # utils.log("Room {} goes to state {}".format(rm.id, rm.state), f=next_state)
    rm.save(update_fields=['state', 'opened'])


def set_rm_timestep(rm, t, tuto):

    if tuto:
        rm.tutorial_t = t
        rm.save(update_fields=['tutorial_t'])

    else:
        rm.t = t
        rm.save(update_fields=['t'])

    return rm
