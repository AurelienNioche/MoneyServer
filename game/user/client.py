import numpy as np

from parameters import parameters

from game.models import User, Room, Choice
import game.room.state


def connect(device_id):

    rm = Room.objects.filter(opened=True).first()

    if rm:

        u = User.objects.filter(device_id=device_id, room_id=rm.id).first()

        if not u:

            u, made_choice, good_in_hand, desired_good = _create_new_user(rm, device_id)

        else:

            goods = get_user_last_known_goods(u, rm, rm.t)
            made_choice = goods["made_choice"]
            good_in_hand = goods["good_in_hand"]
            desired_good = goods["desired_good"]

        progress = game.room.state.get_progress_for_current_state(rm)

        # Get relative good_in_hand
        relative_good_in_hand = get_relative_good(u, good_in_hand)

        # only get desired good if it exists
        # (meaning it is a reconnection and not a first connection)
        relative_desired_good = get_relative_good(u, desired_good) if desired_good else None

        return {
            "wait": True if progress != 100 else False,
            "progress": progress,
            "state": rm.state,
            "made_choice": made_choice,
            "score": u.score,
            "good_in_hand": relative_good_in_hand,
            "desired_good": relative_desired_good,
            "t": rm.t,
            "pseudo": u.pseudo,
            "user_id": u.id
        }


def _create_new_user(rm, device_id):
    """
    Creates a new user and returns goods he is carrying
    :param rm:
    :param device_id:
    :return: user object (django model),
    choice_made (bool), good_in_hand, desired_good
    """

    made_choice = False
    good_in_hand = _get_user_production_good(rm)
    desired_good = None
    consumption_good = (good_in_hand + 1) % 2

    pseudo = np.random.choice(parameters.pseudo)

    while User.objects.filter(pseudo=pseudo, room_id=rm.id).first():
        pseudo = np.random.choice(parameters.pseudo)

    u = User(
        device_id=device_id,
        pseudo=pseudo,
        room_id=rm.id,
        production_good=good_in_hand,
        consumption_good=consumption_good,
        tutorial_done=False,
        score=0,
    )

    u.save()

    return u, made_choice, good_in_hand, desired_good


def get_user_last_known_goods(u, rm, t):
    """
    Get user' goods for t.
    In the event it does not exists,
    it means that the user did not make its choice yet.
    Then returns last known good_in_hand, precising that
    choice_made is False and desired_good is None because
    it does not exist yet.
    :param u:
    :param rm:
    :param t:
    :return: choice_made, good_in_hand, desired_good
    """

    goods = {}

    choice = Choice.objects.filter(user_id=u.id, room_id=rm.id, t=t).first()

    if choice:
        # Choice has been made, return choice data
        goods["made_choice"] = True
        goods["good_in_hand"] = choice.good_in_hand
        goods["desired_good"] = choice.desired_good

    else:
        # Choice has not been made, return last time choice
        goods["made_choice"] = False
        goods["desired_good"] = None

        last_choice = Choice.objects.filter(user_id=u.id, room_id=rm.id, t=t-1).first()

        if last_choice:

            # If exchange was a success, return desired good as good in hand.
            if last_choice.success:
                goods["good_in_hand"] = choice.desired_good

            # Else return last good in hand
            else:
                goods["good_in_hand"] = choice.good_in_hand

        # If last_choice is not found, it means it means that t <= 1
        # and user has in hand production good
        else:
            goods["good_in_hand"] = u.production_good

    return goods


def submit_survey(user_id, age, gender):

    u = User.objects.filter(id=user_id).first()

    if u:

        if u.age is None and u.gender is None:
            u.age = age
            u.gender = gender
            u.save(update_fields=["age", "gender"])

    else:
        raise Exception("Error: User tries to submit survey but does not exit in database.")


def _get_user_production_good(rm):

    for g, n in enumerate([rm.x0, rm.x1, rm.x2]):

        n_user = User.objects.filter(room_id=rm.id, production_good=g).count()

        if n_user < n:

            return g

    raise Exception("Error: too much players.")


def get_relative_good(u, good):

    goods = np.array([0, 1, 2])

    cond0 = goods != u.production_good
    cond1 = goods != u.consumption_good
    medium_good = goods[cond0 * cond1][0]

    mapping = {
        0: u.production_good,
        1: u.consumption_good,
        2: medium_good
    }

    return int(mapping.get(good))


def get_absolute_good(u, good):

    goods = np.array([0, 1, 2])

    cond0 = goods != u.production_good
    cond1 = goods != u.consumption_good
    medium_good = goods[cond0 * cond1][0]

    mapping = {
        u.production_good: 0,
        u.consumption_good: 1,
        medium_good: 2,
    }

    return int(mapping.get(good))


def submit_tutorial_done(user_id):

    u = User.objects.filter(id=user_id).first()

    if not u:
        raise Exception("Error in 'submit_tutorial_progression': User not found.")

    u.tutorial_done = True

    u.save(update_fields=["tutorial_done"])
