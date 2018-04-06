import numpy as np

from parameters import parameters

from game.models import User, Room, Choice
import game.room.state


def connect(device_id):

    rm = Room.objects.filter(opened=True).first()

    if rm:

        u = User.objects.filter(device_id=device_id, room_id=rm.id).first()

        progress = game.room.state.get_progress_for_current_state(rm)
        made_choice, desired_good, good_in_hand = get_user_choice(u, rm)

        if not u:

            consumption_good = (good_in_hand + 1) % 2

            pseudo = np.random.choice(parameters.pseudo)

            while User.objects.filter(pseudo=pseudo, room_id=rm.id).first():
                pseudo = np.random.choice(parameters.pseudo)

            u = User(
                device_id=device_id,
                pseudo=pseudo,
                room_id=rm.id,
                state=game.room.state.welcome,
                production_good=good_in_hand,
                consumption_good=consumption_good,
                tutorial_progression=0
            )

            u.save()

        relative_good_in_hand = get_relative_good(u, good_in_hand)
        relative_desired_good = get_relative_good(u, desired_good)

        return (
            True if progress != 100 else False,
            progress,
            u.state,
            made_choice,
            u.score,
            relative_good_in_hand,
            relative_desired_good,
            rm.t,
            u.pseudo,
            u.id
        )


def get_user_choice(u, rm):

    choice = Choice.objects.filter(
        user_id=u.id,
        room_id=rm.id,
        t=rm.t
    ).first()

    if choice.desired_good:
        return True, choice.desired_good, choice.good_in_hand

    else:
        return False, 0, get_user_production_good(rm)


def get_user_production_good(rm):

    for g, n in zip((0, 1, 2), (rm.x0, rm.x1, rm.x2)):

        n_user = User.objects.filter(room_id=rm.id, production_good=g).count()

        if n_user < n:

            return g

    raise Exception("Error: too much players")


def get_relative_good(u, good):

    goods = np.array([0, 1, 2])

    cond0 = goods != u.production_good
    cond1 = goods != u.consumption_good

    map = {
        0: u.production_good,
        1: u.consumption_good,
        2: goods[cond0 * cond1][0]
    }

    return map[good]


def get_absolute_good(u, good):

    goods = np.array([0, 1, 2])

    cond0 = goods != u.production_good
    cond1 = goods != u.consumption_good

    map = {
        u.production_good: 0,
        u.consumption_good: 1,
        goods[cond0 * cond1][0]: 2,
    }

    return map[good]



