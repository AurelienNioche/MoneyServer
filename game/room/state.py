from game.models import User, Choice, TutorialChoice
from collections import namedtuple


# Globals
States = namedtuple('States', ['welcome', 'survey', 'tutorial', 'game', 'end'])
states = States(welcome='welcome', survey='survey', tutorial='tutorial', game='game', end='end')


def get_progress_for_choices(rm, t, tuto=False):

    table = TutorialChoice if tuto else Choice

    n_choices = table.objects.filter(room_id=rm.id, t=t).exclude(user_id=None).count()
    progress = round(n_choices / rm.n_user * 100)

    return progress


def next_state(rm):

    try:

        # A bit hacky/dirty, TODO: find another solution
        rm.state = states[states.index(rm.state) + 1]
        rm.save(update_fields=['state'])

    except IndexError:

        raise Exception("Error in 'game.room.state': Going to next state is impossible, state does not exist.")


def set_rm_timestep(rm, t):

    if rm.state == states.tutorial:
        rm.tutorial_t = t
        rm.save(update_fields=['tutorial_t'])

    else:
        rm.t = t
        rm.save(update_fields=['t'])
