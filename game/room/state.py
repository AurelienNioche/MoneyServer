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
        n_user = User.objects.filter(room_id=rm.id).exclude(age=None).count()

        progress = round(n_user / rm.n_user * 100)

    elif rm.state == states.tutorial:

        progress = round(rm.tutorial_t / rm.tutorial_t_max * 100)

    elif rm.state == states.game:

        progress = round(rm.t / rm.t_max * 100)

    else:

        raise Exception("Error in 'game.room.state': Bad state")

    if progress == 100:
        _next_state(rm)

    return progress


def get_progress_for_choices(rm, t):

    n_choices = Choice.objects.filter(room_id=rm.id, t=t).exclude(user_id=None).count()
    progress = round(n_choices / rm.n_user * 100)

    if n_choices == rm.n_user:
        _increment_timestep(rm)
        t += 1

    return progress, t


def verify_rm_state_and_u_demand_compatibility(rm, user_demand):

    mapping = {
        states.welcome: ["init"],
        states.tutorial: ["tutorial_choice", "tutorial_done"],
        states.survey: ["survey"],
        states.game: ["choice"],
        states.end: []
    }

    return user_demand in mapping[rm.state]


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