from django.db import transaction
import itertools

import numpy as np

from game.models import User, Room, Choice
import game.user.client
import game.room.state
import game.views


def get_room(room_id):

    rm = Room.objects.filter(id=room_id).first()

    if not rm:
        raise Exception("Error: Room not found.")

    return rm


def get_progression(u, rm, t, tuto=False):

    if u.state == game.room.state.states.game:

        return game.room.state.get_progress_for_choices(rm=rm, t=t, tuto=tuto)

    else:

        return game.user.state.get_progress_for_current_state(u=u, rm=rm)


def state_verification(u, rm, progress, t, demand, success=None):

    """

    Manage room and user states
    depending on demand made by client.

    """

    if demand == game.views.init:

        if u.state == game.room.state.states.welcome:

            wait = progress != 100

            if not wait:

                if rm.state == game.room.state.states.welcome:
                    game.room.state.next_state(
                        rm=rm,
                        state=game.room.state.states.survey
                    )

                if u.state == game.room.state.states.welcome:
                    u = game.user.state.next_state(
                        u=u,
                        state=game.room.state.states.survey
                    )

        else:
            wait = False
        
        return wait, u.state

    elif demand == game.views.survey:

        if u.state == game.room.state.states.survey:

            wait = progress != 100

            if not wait:

                if rm.state == game.room.state.states.survey:
                    game.room.state.next_state(
                        rm=rm,
                        state=game.room.state.states.tutorial
                    )

                if u.state == game.room.state.states.survey:
                    u = game.user.state.next_state(
                        u=u,
                        state=game.room.state.states.tutorial,
                    )
        else:
            wait = False

        return wait, u.state

    elif demand == game.views.tutorial_choice:

        t += 1
        wait = False
        end = t == rm.tutorial_t_max

        return wait, t, end

    elif demand == game.views.tutorial_done:

        if u.state == game.room.state.states.tutorial:
            wait = progress != 100

            if not wait:

                if rm.state == game.room.state.states.tutorial:

                    game.room.state.next_state(
                        rm=rm,
                        state=game.room.state.states.game
                    )

                if u.state == game.room.state.states.tutorial:
                    u = game.user.state.next_state(
                        u=u,
                        state=game.room.state.states.game
                    )

        else:
            wait = False

        return wait, u.state

    elif demand == game.views.choice:

        wait = progress != 100 or success is None
        t += not wait
        rm = game.room.state.set_rm_timestep(rm=rm, t=t, tuto=False)

        end = rm.t == rm.t_max

        if end:

            if rm.state == game.room.state.states.game:
                game.room.state.next_state(
                    rm=rm,
                    state=game.room.state.states.end
                )

            if u.state == game.room.state.states.game:
                game.user.state.next_state(
                    u=u,
                    state=game.room.state.states.end
                )

        return wait, t, end


def matching(rm, t):

    # List possible markets
    markets = itertools.combinations_with_replacement(range(rm.n_type), r=2)

    with transaction.atomic():

        # Get choices for room and time
        # No wait argument allows to raise an exception when another process
        # tries to select these entries
        choices = \
            Choice.objects.all().select_for_update(nowait=True).filter(room_id=rm.id, t=t, success=None)

        if choices:

            for g1, g2 in markets:

                # Get exchanges for goods e.g 0, 1 and 1, 0
                pools = [
                    list(choices.filter(desired_good=g1, good_in_hand=g2).only('success', 'user_id')),
                    list(choices.filter(desired_good=g2, good_in_hand=g1).only('success', 'user_id'))
                ]

                # We sort 'pools' of choices in order to get the shortest pool first
                idx_min, idx_max = np.argsort([len(p) for p in pools])

                # Then we have two pools with different sizes
                min_pool, max_pool = pools[idx_min], pools[idx_max]

                # Randomize the max pool
                np.random.shuffle(max_pool)

                # The firsts succeed to exchange
                for c1, c2 in zip(min_pool, max_pool):

                    c1.success = True
                    c2.success = True
                    c1.save(update_fields=["success"])
                    c2.save(update_fields=["success"])

                    # Compute score and set the resulting good in hand
                    # for each exchange.
                    _compute_score_and_final_good(c=c1)
                    _compute_score_and_final_good(c=c2)

                idx = len(min_pool)

                # The lasts fail
                for c in max_pool[idx:]:

                    c.success = False
                    c.save(update_fields=["success"])

                    _compute_score_and_final_good(c)


def _compute_score_and_final_good(c):

    u = User.objects.select_for_update().filter(id=c.user_id).first()

    if u:

        next_choice = Choice.objects.select_for_update().filter(
            player_id=u.player_id,
            t=c.t+1,
            room_id=c.room_id
        ).first()

        if c.success:

            # If desired good is consumption good
            # then consume and increase score
            if u.consumption_good == c.desired_good:

                if next_choice:
                    next_choice.good_in_hand = u.production_good

                u.score += 1
                u.save(update_fields=["score"])

            # else the resulting is the desired good
            else:
                
                if next_choice:
                    next_choice.good_in_hand = c.desired_good

        # If the exchange did not succeed then
        # the resulting good is the good in hand
        else:

            if next_choice:
                next_choice.good_in_hand = c.good_in_hand

        if next_choice:
            next_choice.save(update_fields=["good_in_hand"])

    else:
        raise Exception("User is not found for that exchange.")
