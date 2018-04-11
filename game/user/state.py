from game.room.state import states
from game.models import User

from utils import utils


def get_progress_for_current_state(rm, u):

    # ----- Get progress ----------------------------------------------- #
    if u.state == states.welcome:

        # Count users assigned to the room
        n_user = User.objects.filter(room_id=rm.id).count()

        return round(n_user / rm.n_user * 100)

    elif u.state == states.survey:

        # Get player with age and gender assigned
        n_user = User.objects.filter(room_id=rm.id).exclude(age=None).count()

        return round(n_user / rm.n_user * 100)

    elif u.state == states.tutorial:

        return round(rm.tutorial_t / rm.tutorial_t_max * 100)

    elif u.state in (states.game, states.end, ):

        return round(rm.t / rm.t_max * 100)

    else:

        raise Exception("Error in 'game.user.state': Bad state")


def next_state(u):

    try:

        # A bit hacky/dirty, TODO: find another solution
        u.state = states[states.index(u.state) + 1]
        utils.log("User {} goes to state {}".format(u.pseudo, u.state), f=next_state)
        u.save(update_fields=['state'])

    except IndexError:

        raise Exception("Error in 'game.user.state': Going to next state is impossible, state does not exist.")

