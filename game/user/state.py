from game.room.state import states
from game.models import User


def get_progress_for_current_state(rm, u):

    # ----- Get progress ----------------------------------------------- #

    if u.state == states.WELCOME:

        # Count users assigned to the room
        n_user = User.objects.filter(room_id=rm.id).count()

        return round(n_user / rm.n_user * 100)

    elif u.state == states.SURVEY:

        # Get player with age and gender assigned
        n_user = User.objects.filter(room_id=rm.id).exclude(age=None).count()

        return round(n_user / rm.n_user * 100)

    elif u.state == states.TRAINING:

        if u.training_done:

            n_user = User.objects.filter(room_id=rm.id, training_done=True).count()

            return round(n_user / rm.n_user * 100)

        else:

            # During training, progression is always 100 because
            # players don't wait for other's choices
            return 100

    elif u.state in (states.GAME, states.END, ):

        return round(rm.t / rm.t_max * 100)

    else:

        raise Exception("Error in 'game.user.state': Bad state")


def next_state(u, state):
    u.state = state
    # utils.log("User {} goes to state {}".format(u.pseudo, u.state), f=next_state)
    u.save(update_fields=['state'])

    return u

