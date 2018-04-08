from django.db.models import Q
import numpy as np

from game.models import User, Room, Choice
import game.user.client
import game.room.state


def get_progression(user_id, t):

    u = User.objects.get(id=user_id)
    rm = Room.objects.get(id=u.room_id)

    progress = game.room.state.get_progress_for_current_state(rm)
    has_to_wait = True if progress != 100 else False

    if rm.state == game.room.state.states.game:
        choice_progress = game.room.state.get_progress_for_choices(rm, t)
    else:
        choice_progress = None

    return progress, has_to_wait, choice_progress


def submit_choice(desired_good, user_id, t):

    u = User.objects.get(id=user_id)
    rm = Room.objects.get(id=u.room_id)

    # ------ Get user good in hand -------- #
    last_choice = Choice.objects.filter(t=t-1, user_id=user_id).first()

    if last_choice:

        if last_choice.desired_good == u.consumption_good and last_choice.success:
            good_in_hand = u.production_good

        elif last_choice.success:
            good_in_hand = last_choice.desired_good

        else:
            good_in_hand = last_choice.good_in_hand

    # if t == 0
    else:

        good_in_hand = u.production_good

    # ------------------------------------- #

    # ------- Check if current choice has been set or not ------ #

    current_choice = Choice.objects.filter(room_id=rm.id, t=t, user_id=u.id).first()

    if current_choice:

        # If matching has been done
        if current_choice and current_choice.success is not None:

            return current_choice.success

        else:

            _matching(rm, t)
            return None

    # If choice entry is not filled for this t
    else:

        current_choice = Choice.objects.filter(room_id=rm.id, t=t, user_id=None).first()

        current_choice.user_id = user_id
        current_choice.desired_good = game.user.client.get_absolute_good(u, desired_good)
        current_choice.good_in_hand = good_in_hand

        current_choice.save(update_fields=["user_id", "desired_good", "good_in_hand"])

        return None


def _matching(rm, t):

    # List possible markets
    markets = (0, 1), (1, 2), (2, 0)

    # Get choices for room and time
    choices = Choice.objects.filter(room_id=rm.id, t=t)

    for g1, g2 in markets:

        pool1 = choices.filter(Q(desired_good=g1) | Q(good_in_hand=g2)).only('success')
        pool2 = choices.filter(Q(desired_good=g2) | Q(good_in_hand=g1)).only('success')

        pools = [pool1, pool2]

        # We sort pools in order to get the shortest pool first
        idx = np.argsort([p.count() for p in pools])
        min_pool, max_pool = pools[idx]

        # Shuffle the max pool
        max_pool = max_pool.order_by('?')

        # The firsts succeed
        for c1, c2 in zip(min_pool, max_pool):
            c1.success = True
            c2.success = True
            c1.save(update_fields=["success"])
            c2.save(update_fields=["success"])

        # The lasts fail
        for c in max_pool.exclude(success=True):
            c.success = False
            c.save(update_fields=["success"])
