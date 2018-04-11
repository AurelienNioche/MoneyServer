from django.db import transaction
import numpy as np

from parameters import parameters

from game.models import User, Room, Choice, TutorialChoice
import game.room.state
import game.user.state


def connect(device_id):

    with transaction.atomic():
        rm = Room.objects.select_for_update().filter(opened=True).first()

    if rm:

        u = User.objects.filter(device_id=device_id, room_id=rm.id).first()

        if not u:

            u, good_in_hand = _create_new_user(rm, device_id)

            choice_made = None
            desired_good = None

            tuto_choice_made = None
            tuto_good_in_hand = u.production_good
            tuto_desired_good = None

        else:

            goods = get_user_last_known_goods(u=u, rm=rm, t=rm.t)

            choice_made = goods["choice_made"]
            good_in_hand = goods["good_in_hand"]
            desired_good = goods["desired_good"]

            tuto_goods = get_user_last_known_goods(u=u, rm=rm, t=rm.t, tuto=True)

            tuto_choice_made = tuto_goods["choice_made"]
            tuto_good_in_hand = tuto_goods["good_in_hand"]
            tuto_desired_good = tuto_goods["desired_good"]

        # Get relative good_in_hand
        relative_good_in_hand = get_relative_good(u, good_in_hand)
        relative_tuto_good_in_hand = get_relative_good(u, tuto_good_in_hand)

        # only get desired good if it exists
        # (meaning it is a reconnection and not a first connection)
        relative_desired_good = get_relative_good(u, desired_good) if desired_good else None
        relative_tuto_desired_good = get_relative_good(u, tuto_desired_good) if tuto_desired_good else None

        return {
            "state": u.state,
            "choice_made": choice_made,
            "tuto_choice_made": tuto_choice_made,
            "score": u.score,
            "good_in_hand": relative_good_in_hand,
            "tuto_good_in_hand": relative_tuto_good_in_hand,
            "desired_good": relative_desired_good,
            "tuto_desired_good": relative_tuto_desired_good,
            "t": rm.t,
            "t_max": rm.t_max,
            "tuto_t_max": rm.tutorial_t_max,
            "tuto_t": rm.tutorial_t,
            "pseudo": u.pseudo,
            "user_id": u.id
        }, u, rm

    else:
        raise Exception("Error: No room found.")


@transaction.atomic
def get_user(user_id):
    u = User.objects.select_for_update().filter(id=user_id).first()
    if not u:
        raise Exception("Error: User not found.")
    return u


def get_user_last_known_goods(u, rm, t, tuto=False):
    """
    Get user' goods for t.
    In the event it does not exists,
    it means that the user did not make its choice yet.
    Then returns last known good_in_hand, precising that
    choice_made is False and desired_good is None because
    it does not exist yet.
    :param u: user
    :param rm: room
    :param t: time
    :param tuto: is it tutorial or not
    :return: choice_made, good_in_hand, desired_good
    """

    # Get the right table
    table = TutorialChoice if tuto else Choice

    goods = {}

    choice = table.objects.filter(user_id=u.id, room_id=rm.id, t=t).first()

    if choice:
        # Choice has been made, return choice data
        goods["choice_made"] = True
        goods["good_in_hand"] = choice.good_in_hand
        goods["desired_good"] = choice.desired_good

    else:
        # Choice has not been made, return last time choice
        goods["choice_made"] = False
        goods["desired_good"] = None

        last_choice = table.objects.filter(user_id=u.id, room_id=rm.id, t=t-1).first()

        if last_choice:

            # If exchange was a success, return desired good as good in hand.
            if last_choice.success:
                goods["good_in_hand"] = last_choice.desired_good

            # Else return last good in hand
            else:
                goods["good_in_hand"] = last_choice.good_in_hand

        # If last_choice is not found, it means it means that t <= 1
        # and user has in hand production good
        else:
            goods["good_in_hand"] = u.production_good

    return goods


def submit_survey(u, age, gender):

    # if survey is not already completed
    if u.age is None and u.gender is None:
        u.age = age
        u.gender = gender
        u.save(update_fields=["age", "gender"])


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

    # np.int64 is not json serializable
    return int(mapping[good])


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

    # np.int64 is not json serializable
    return int(mapping[good])


def submit_tutorial_done(u):

    u.tutorial_done = True

    u.save(update_fields=["tutorial_done"])


def submit_tutorial_choice(u, rm, desired_good, t):

    """
    TODO: Increase indirect exchange prob of success
    In order to make those two kind of strategy equivalent
    :param desired_good:
    :param u:
    :param rm:
    :param desired_good:
    :param t:
    :return:
    """

    choice = TutorialChoice.objects.filter(room_id=rm.id, user_id=u.id, t=t).first()

    if not choice:

        with transaction.atomic():

            choice = TutorialChoice.objects.select_for_update()\
                    .filter(room_id=u.room_id, user_id=None, t=t).first()

            if not choice:
                raise Exception("Error in 'submit_tutorial_choice': Did not found an empty choice entry.")

            choice.user_id = u.id
            choice.desired_good = get_absolute_good(good=desired_good, u=u)
            choice.good_in_hand = get_user_last_known_goods(u=u, rm=rm, t=t, tuto=True)["good_in_hand"]
            choice.success = np.random.choice([False, True])
            u.score += choice.success
            choice.save(update_fields=['user_id', 'success', 'good_in_hand', 'desired_good'])
            u.save(update_fields=["score"])

            return choice.success, u.score
    else:
        return choice.success, u.score


def _create_new_user(rm, device_id):

    """
    Creates a new user and returns goods he is carrying
    :param rm:
    :param device_id:
    :return: user object (django model),
    choice_made (bool), good_in_hand, desired_good
    """

    good_in_hand = _get_user_production_good(rm)
    consumption_good = (good_in_hand + 1) % 2

    with transaction.atomic():

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
            tutorial_score=0,
            state=game.room.state.states.welcome
        )

        u.save()

    return u, good_in_hand


def _get_user_production_good(rm):

    for g, n in enumerate([rm.x0, rm.x1, rm.x2]):

        n_user = User.objects.filter(room_id=rm.id, production_good=g).count()

        if n_user < n:

            return g

    raise Exception("Error: too much players.")

