from django.db import transaction

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

    if u.state in (game.room.state.states.game, ):

        return game.room.state.get_progress_for_choices(rm=rm, t=t, tuto=tuto)

    else:

        return game.user.state.get_progress_for_current_state(u=u, rm=rm)


def state_verification(u, rm, progress, t, demand):

    if demand in (game.views.tutorial_choice, ):

        t += 1
        wait = False
        end = t == rm.tutorial_t_max

        return wait, t, end

    elif demand in (game.views.choice, ):

        t = t + 1 if progress == 100 else t
        rm = game.room.state.set_rm_timestep(rm=rm, t=t, tuto=False)
        wait = False if progress == 100 else True

        end = rm.t == rm.t_max

        if end:

            if rm.state in (game.room.state.states.game, ):
                game.room.state.next_state(
                    rm=rm,
                    state=game.room.state.states.end
                )

            if u.state in (game.room.state.states.game, ):
                game.user.state.next_state(
                    u=u,
                    state=game.room.state.states.end
                )

        return wait, t, end

    elif demand in (game.views.init, ):

        if progress == 100:

            if rm.state in (game.room.state.states.welcome, ):
                game.room.state.next_state(
                    rm=rm,
                    state=game.room.state.states.survey
                )

            if u.state in (game.room.state.states.welcome, ):
                u = game.user.state.next_state(
                    u=u,
                    state=game.room.state.states.survey
                )

            return False, u.state

        else:

            return True, u.state

    elif demand in (game.views.survey, ):

        if progress == 100:

            if rm.state in (game.room.state.states.survey, ):
                game.room.state.next_state(
                    rm=rm,
                    state=game.room.state.states.tutorial
                )

            if u.state in (game.room.state.states.survey, ):
                u = game.user.state.next_state(
                    u=u,
                    state=game.room.state.states.tutorial,
                )

            return False, u.state

        else:

            return True, u.state

    elif demand in (game.views.tutorial_done, ):

        if progress == 100:

            if rm.state in (game.room.state.states.tutorial, ):

                game.room.state.next_state(
                    rm=rm,
                    state=game.room.state.states.game
                )

            if u.state in (game.room.state.states.tutorial, ):
                u = game.user.state.next_state(
                    u=u,
                    state=game.room.state.states.game
                )

            return False, u.state

        else:
            return True, u.state


def matching(rm, t):

    # List possible markets
    markets = (0, 1), (1, 2), (2, 0)

    with transaction.atomic():

        # Get choices for room and time
        # No wait argument allows to raise an exception when another process
        # tries to select these entries
        choices = Choice.objects.select_for_update(nowait=True).filter(room_id=rm.id, t=t, success=None)

        for g1, g2 in markets:

            # Get exchanges for goods e.g 0, 1 and 1, 0
            pools = [
                choices.filter(desired_good=g1, good_in_hand=g2).only('success', 'user_id'),
                choices.filter(desired_good=g2, good_in_hand=g1).only('success', 'user_id')
            ]

            # We sort 'pools' of choices in order to get the shortest pool first
            idx_min, idx_max = np.argsort([p.count() for p in pools])
            # Then we have two pools with different sizes
            min_pool, max_pool = pools[idx_min], pools[idx_max]

            # Randomize the max pool
            max_pool = max_pool.order_by('?')

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

            idx = min_pool.count()

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

        if not next_choice:
            raise Exception("t {} does not exist".format(c.t+1))

        if c.success:

            # If desired good is consumption good
            # then consume and increase score
            if u.consumption_good == c.desired_good:
                next_choice.good_in_hand = u.production_good
                u.score += 1
                u.save(update_fields=["score"])

            # else the resulting is the desired good
            else:
                print("WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWw")
                next_choice.good_in_hand = c.desired_good

            next_choice.save(update_fields=["good_in_hand"])

        # If the exchange did not succeed then
        # the resulting good is the good in hand
        else:

            next_choice.good_in_hand = c.good_in_hand
            next_choice.save(update_fields=["good_in_hand"])

    else:
        raise Exception("User is not found for that exchange.")
