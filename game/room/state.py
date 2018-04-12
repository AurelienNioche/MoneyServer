from game.models import Choice, TutorialChoice
from collections import namedtuple

from utils import utils

# Globals
States = namedtuple('States', ['welcome', 'survey', 'tutorial', 'game', 'end'])
states = States(welcome='welcome', survey='survey', tutorial='tutorial', game='game', end='end')


def get_progress_for_choices(rm, t, tuto=False):

    table = TutorialChoice if tuto else Choice

    n_choices = table.objects.filter(room_id=rm.id, t=t).exclude(user_id=None).count()
    progress = round(n_choices / rm.n_user * 100)

    return progress


def next_state(rm, state):

    rm.state = state

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
