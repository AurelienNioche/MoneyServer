from game.models import User, Choice
from collections import namedtuple


# Globals
States = namedtuple('States', ['welcome', 'survey', 'tutorial', 'game', 'end'])
states = States(welcome='welcome', survey='survey', tutorial='tutorial', game='game', end='end')


def get_progress_for_current_state(rm):

    # ----- Get progress ----------------------------------------------- #
    if rm.state == states.welcome:

        # Count users assigned to the room
        n_user = User.objects.filter(room_id=rm.id).count()

        progress = round(n_user / rm.n_user * 100)

    elif rm.state == states.survey:

        # Get player with age and gender assigned
        n_user = User.objects.filter(room_id=rm.id).exclude(age=None, gender=None).count()

        progress = round(n_user / rm.n_user * 100)

    elif rm.state == states.tutorial:

        n_user = User.objects.filter(room_id=rm.id, tutorial_done=True).count()

        progress = round(n_user / rm.n_user * 100)

    elif rm.state == states.game:

        progress = round(rm.t / rm.ending_t * 100)

    else:

        raise Exception("Error in 'game.room.state': Bad state")

    # ---- Check if progress == 100, if true then go to next state ----- #
    if progress == 100:
        _next_state(rm)

    return progress


def get_progress_for_choices(rm, t):

    n_choices = Choice.objects.filter(room_id=rm.id, t=t).exclude(user_id=None).count()
    progress = round(n_choices / rm.n_user * 100)

    if progress == 100:
        _increment_timestep(rm)

    return progress


def _next_state(rm):

    try:

        # A bit hacky/dirty, TODO: find another solution
        rm.state = states[states.index(rm.state) + 1]
        rm.save(update_fields=['state'])

    except IndexError:

        raise Exception("Error in 'game.room.state': Going to next state is impossible, state does not exist.")


def _increment_timestep(rm):
    rm.t += 1
    rm.save(update_fields=['t'])