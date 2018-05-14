from game.models import Choice, TutorialChoice
from collections import namedtuple

# Global states
States = namedtuple(
    'States',
    ['WELCOME', 'SURVEY', 'TRAINING', 'GAME', 'END']
)

states = States(
    WELCOME='welcome',
    SURVEY='survey',
    TRAINING='training',
    GAME='game',
    END='end'
)


demand_state_mapping = {
    'init': states.WELCOME,
    'survey': states.SURVEY,
    'training': states.TRAINING,
    'training_choice': states.TRAINING,
    'training_done': states.TRAINING,
    'choice': states.GAME
}


def get_progress_for_choices(rm, t, tuto=False):

    table = TutorialChoice if tuto else Choice
    n_choices = table.objects.filter(room_id=rm.id, t=t).exclude(desired_good=None).count()

    return round(n_choices / rm.n_user * 100)


def next_state(rm, state):

    rm.state = state

    # If room's state is end
    # definitely close the room
    if state == states.END:
        rm.opened = False

    # utils.log("Room {} goes to state {}".format(rm.id, rm.state), f=next_state)
    rm.save(update_fields=['state', 'opened'])


def set_rm_timestep(rm, t, tuto):

    if tuto:
        rm.training_t = t
        rm.save(update_fields=['training_t'])

    else:
        rm.t = t
        rm.save(update_fields=['t'])

    return rm
