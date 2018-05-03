from django.db import transaction
import django.db.utils
import psycopg2
import numpy as np

from parameters import parameters

from game.models import User, Room, Choice, TutorialChoice
import game.room.state
import game.room.client
import game.user.state


# ------------------------------  Public functions (called by views) ----------------------------------- #

@transaction.atomic
def get_user(user_id):
    u = User.objects.select_for_update().filter(id=user_id).first()
    if not u:
        raise Exception("Error: User not found.")
    return u


def connect(device_id, skip_survey, skip_tutorial):

    with transaction.atomic():
        # Get opened room
        rooms = Room.objects.select_for_update().all()
        rm = rooms.filter(opened=True).first()

        if not rm:

            # If no room create room dynamically (if auto_room parameter is enabled)
            # Else an exception is raised!
            rm = game.room.client.create_room()

    u = User.objects.filter(device_id=device_id, room_id=rm.id).first()

    if not u:

        u = _create_new_user(rm, device_id)

        choice_made = False
        desired_good = None
        good_in_hand = u.production_good

        tuto_choice_made = False
        tuto_desired_good = None
        tuto_good_in_hand = u.production_good

    else:

        choice_made, good_in_hand, desired_good = \
            _get_user_last_known_goods(u=u, rm=rm, t=rm.t)

        tuto_choice_made, tuto_good_in_hand, tuto_desired_good = \
            _get_user_last_known_goods(u=u, rm=rm, t=rm.tutorial_t, tuto=True)

    # Get relative good_in_hand
    relative_good_in_hand = _get_relative_good(u=u, good=good_in_hand, rm=rm)
    relative_tuto_good_in_hand = _get_relative_good(u=u, good=tuto_good_in_hand, rm=rm)

    # only get desired good if it exists
    # (meaning it is a reconnection and not a first connection)
    relative_desired_good = \
        _get_relative_good(u=u, good=desired_good, rm=rm)\
        if desired_good is not None else -2

    relative_tuto_desired_good = \
        _get_relative_good(u=u, good=tuto_desired_good, rm=rm)\
        if tuto_desired_good is not None else -2

    skip_state = _handle_skip_options(
        u=u,
        rm=rm,
        skip_tutorial=skip_tutorial,
        skip_survey=skip_survey
    )

    info = {
        "pseudo": u.pseudo,
        "userId": u.id,

        "step": u.state if not skip_state else skip_state,

        "choiceMade": choice_made,
        "trainingChoiceMade": tuto_choice_made,

        "score": u.score,

        "nGood": rm.n_type,

        "t": rm.t,
        "tMax": rm.t_max,
        "goodInHand": relative_good_in_hand,
        "goodDesired": relative_desired_good,

        "trainingGoodInHand": relative_tuto_good_in_hand,
        "trainingGoodDesired": relative_tuto_desired_good,
        "trainingTMax": rm.tutorial_t_max,
        "trainingT": rm.tutorial_t,
        "trainingScore": u.tutorial_score,

        "skipSurvey": skip_survey,
        "skipTutorial": skip_tutorial
    }

    return info, u, rm


def submit_survey(u, age, gender):

    # if survey is not already completed
    if u.age is None and u.gender is None:
        u.age = age
        u.gender = gender
        u.save(update_fields=["age", "gender"])


def submit_tutorial_done(u):

    if not u.tutorial_done:

        u.tutorial_done = True
        u.save(update_fields=["tutorial_done"])

    return u


def submit_choice(rm, u, desired_good, t):

    # ------- Check if current choice has been set or not ------ #

    current_choice = Choice.objects.filter(room_id=rm.id, t=t, user_id=u.id).first()

    if not current_choice:

        _set_current_choice(rm=rm, u=u, desired_good=desired_good, t=t)

    elif current_choice.success is not None:
        return current_choice.success, u.score

    # ---------------------------------------------------------- #

    # Does the player trigger matching?
    _triggers_matching(rm=rm, t=t)

    # Reload choice and send infos to client
    choice = Choice.objects.filter(user_id=u.id, room_id=rm.id, t=t).first()
    u = User.objects.filter(id=u.id).first()

    return -2 if choice.success is None else choice.success, u.score


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

        choice = TutorialChoice.objects.filter(room_id=u.room_id, player_id=u.player_id, t=t).first()

        if not choice:
            raise Exception("Error in 'submit_tutorial_choice': Did not found a choice entry.")

        _check_choice_validity(u=u, choice=choice, desired_good=desired_good)

        choice.user_id = u.id
        choice.desired_good = desired_good
        choice.success = bool(np.random.choice([False, True]))

        #  --------------------------------------------------------------------------------------------- #

        if choice.success:

            if choice.desired_good == u.consumption_good:
                good_in_hand = u.production_good
            else:
                good_in_hand = desired_good

        else:

            good_in_hand = choice.good_in_hand

        next_choice = TutorialChoice.objects.filter(room_id=rm.id, player_id=u.player_id, t=t+1).first()

        if next_choice:
            next_choice.good_in_hand = good_in_hand
            next_choice.save(update_fields=['good_in_hand'])

        #  --------------------------------------------------------------------------------------------- #

        u.tutorial_score += choice.success
        choice.save(update_fields=['user_id', 'success', 'desired_good'])
        u.save(update_fields=["tutorial_score"])

    return choice.success, u.tutorial_score

# ------------------------------  Private functions (called inside the script) ----------------------------------- #


def _triggers_matching(rm, t):

    """
    Checks if user is the last
    one to record its choice.
    If so, he triggers the matching.
    """

    n = Choice.objects.filter(room_id=rm.id, t=t).exclude(desired_good=None).count()

    # Do matching if all users made their choice
    if n == rm.n_user:

        try:
            game.room.client.matching(rm=rm, t=t)

        except (psycopg2.OperationalError, django.db.utils.OperationalError):
            # If an error is raised
            # It means that another player has launched the matching
            # Then do nothing
            pass


def _set_current_choice(rm, u, desired_good, t):

    current_choice = Choice.objects.filter(room_id=rm.id, t=t, player_id=u.player_id).first()

    _check_choice_validity(u=u, choice=current_choice, desired_good=desired_good)

    current_choice.user_id = u.id
    current_choice.desired_good = desired_good

    current_choice.save(update_fields=["user_id", "desired_good"])


def _create_new_user(rm, device_id):

    """
    Creates a new user and returns its instance
    :param rm:
    :param device_id:
    :return: user object (django model),
    """

    with transaction.atomic():

        users = User.objects.select_for_update().all()

        player_id = users.filter(room_id=rm.id).count()

        pseudo = parameters.pseudos[player_id]

        u = User(
            device_id=device_id,
            player_id=player_id,
            pseudo=pseudo,
            room_id=rm.id,
            tutorial_done=False,
            score=0,
            tutorial_score=0,
            state=game.room.state.states.welcome
        )

        u.save()

        u.production_good = _get_user_production_good(rm, u)
        u.consumption_good = (u.production_good - 1) % rm.n_type

        u.save(update_fields=["production_good", "consumption_good"])

        return u


def _get_user_production_good(rm, u):

    count_type = [int(i) for i in rm.types.split("/")]

    types = [i for i in range(rm.n_type)
             for _ in range(count_type[i])]

    try:
        return types[u.player_id]

    except IndexError:
        raise Exception("Too much players.")


def get_absolute_good(u, rm, good):

    mapping = np.ones(rm.n_type, dtype=int) * - 1

    mapping[0] = u.production_good
    mapping[1] = u.consumption_good

    # Get medium good
    goods = np.arange(rm.n_type)

    cond0 = goods != u.production_good
    cond1 = goods != u.consumption_good
    medium_goods = np.array(goods[cond0 * cond1])

    a = int(np.sum(mapping != -1))
    b = len(mapping)

    mapping[np.arange(a, b)] = medium_goods

    # np.int64 is not json serializable
    return int(mapping[good])


def _get_relative_good(u, rm, good):

    mapping = np.ones(rm.n_type, dtype=int) * - 1

    mapping[u.production_good] = 0
    mapping[u.consumption_good] = 1

    # Get medium good
    goods = np.arange(rm.n_type)

    cond0 = goods != u.production_good
    cond1 = goods != u.consumption_good
    medium_goods = np.array(goods[cond0 * cond1])

    a = int(np.sum(mapping != -1))
    b = len(mapping)

    mapping[medium_goods] = np.arange(a, b)

    # np.int64 is not json serializable
    return int(mapping[good])


def _get_user_last_known_goods(u, rm, t, tuto=False):

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
    choice = table.objects.filter(user_id=u.id, room_id=rm.id, t=t).first()

    if choice:

        # Choice has been made, return choice data
        choice_made = True
        good_in_hand = choice.good_in_hand
        desired_good = choice.desired_good

    else:

        choice = table.objects.filter(player_id=u.player_id, room_id=rm.id, t=t).first()

        if choice:

            choice_made = False
            good_in_hand = choice.good_in_hand
            desired_good = None

        else:
            raise Exception("Choice cannot be found!")

    return choice_made, good_in_hand, desired_good


def _check_choice_validity(u, choice, desired_good):

    if choice.good_in_hand == desired_good:

        raise Exception(
            f"User {u.pseudo} with id {u.id} can't choose the same good as he is carrying!"
        )

    elif choice.good_in_hand is None:

        raise Exception(
            f"User {u.pseudo} with id {u.id} asks for choice recording but good in hand is None"
        )


def _handle_skip_options(u, rm, skip_tutorial, skip_survey):

    """
    If skip options are enabled
     (in the settings menu located in the admin interface)
    Change room's state as well as users' state.
    """

    if skip_tutorial:
        skip_state = game.room.state.states.game
    elif skip_survey:
        skip_state = game.room.state.states.tutorial
    else:
        skip_state = None

    if skip_state is not None:
        if rm.state != skip_state:
            game.room.state.next_state(rm, skip_state)

        if u.state != skip_state:
            game.user.state.next_state(u, skip_state)

    return skip_state

