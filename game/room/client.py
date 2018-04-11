from django.db import transaction
from django.db.models import Q

from game.models import User, Room, Choice
import game.user.client
import game.room.state


@transaction.atomic
def get_room(room_id):

    rm = Room.objects.select_for_update().filter(id=room_id).first()

    if not rm:
        raise Exception("Error: Room not found.")

    return rm


def get_progression(u, rm, t, tuto=False):

    if u.state in (game.room.state.states.game, game.room.state.states.tutorial):

        return game.room.state.get_progress_for_choices(rm=rm, t=t, tuto=tuto)

    else:

        return game.user.state.get_progress_for_current_state(u=u, rm=rm)


def state_verification(u, rm, progress, t):

    if u.state in (game.room.state.states.game, game.room.state.states.tutorial):

        t = t + 1 if progress == 100 else t
        wait = False if progress == 100 else True

        end = game.user.state.get_progress_for_current_state(u=u, rm=rm) == 100

        if end:

            if u.state == rm.state:
                rm = game.room.state.set_rm_timestep(rm=rm, t=t)
                game.room.state.next_state(rm=rm)

            game.user.state.next_state(u=u)

        return wait, t, end

    else:

        if progress == 100:

            if u.state == rm.state:
                game.room.state.next_state(rm=rm)

            game.user.state.next_state(u=u)

            return False

        else:

            return True


def submit_choice(desired_good, user_id, t):

    u = User.objects.filter(id=user_id).first()
    rm = Room.objects.filter(id=u.room_id).first()

    if not u or not rm:
        raise Exception("Error: Room is {} and user is {}".format(rm, u))

    # ------- Check if current choice has been set or not ------ #

    current_choice = Choice.objects.filter(room_id=rm.id, t=t, user_id=u.id).first()

    if current_choice:

        # If matching has been done
        if current_choice and current_choice.success is not None:
            return current_choice.success, u.score

        else:
            _matching(rm, t)
            return None, u.score

    # If choice entry is not filled for this t
    else:

        current_choice = Choice.objects.select_for_update()\
            .filter(room_id=rm.id, t=t, user_id=None).first()

        current_choice.user_id = user_id

        current_choice.desired_good = \
            game.user.client.get_absolute_good(u=u, good=desired_good)

        current_choice.good_in_hand = \
            game.user.client.get_user_last_known_goods(rm=rm, u=u, t=t-1)["good_in_hand"]

        current_choice.save(update_fields=["user_id", "desired_good", "good_in_hand"])

        return None, u.score


def _matching(rm, t):

    # List possible markets
    markets = (0, 1), (1, 2), (2, 0)

    # Get choices for room and time
    choices = Choice.objects.select_for_update().filter(room_id=rm.id, t=t, success=None)

    for g1, g2 in markets:

        pools = [
            choices.filter(Q(desired_good=g1) | Q(good_in_hand=g2)).only('success', 'user_id'),
            choices.filter(Q(desired_good=g2) | Q(good_in_hand=g1)).only('success', 'user_id')
        ]

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

            _compute_score(u1=c1.user_id, u2=c2.user_id)

        # The lasts fail
        for c in max_pool.exclude(success=True):

            c.success = False
            c.save(update_fields=["success"])


def _compute_score(u1, u2):

    for i in (u1, u2):

        u = User.objects.filter(id=i).first()

        if u:

            u.score += 1
            u.save(update_fields=["score"])

        else:
            raise Exception("Error in '_matching': Users are not found for that exchange.")
