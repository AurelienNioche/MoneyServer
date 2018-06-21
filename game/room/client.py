from django.db import transaction
import itertools

import numpy as np

from game.models import User, Room, Choice, TutorialChoice, Receipt, ConsumerTask
import game.user.client
import game.room.state
import game.room.dashboard
import game.views
import game.params.client

from parameters import parameters


def get_room(room_id):

    rm = Room.objects.filter(id=room_id).first()

    if not rm:
        raise Exception("Room not found.")

    return rm


def get_all_users_that_did_not_receive(room_id, demand, t=None):

    players_that_did_not_receive = Receipt.objects.filter(
            room_id=room_id, demand=demand.__name__, t=t, received=False).values_list('player_id')

    return User.objects.filter(room_id=room_id, player_id__in=players_that_did_not_receive)


def get_all_users(room_id):
    return User.objects.filter(room_id=room_id)


def get_results_for_all_users(room_id, t):

    choices = Choice.objects.filter(room_id=room_id, t=t)
    users = User.objects.filter(room_id=room_id)

    for u in users:

        c = choices.filter(user_id=u.id).first()

        if not c:
            raise Exception(f'Choice from user {u.id} is not found for t={t} after matching.')

        u.success = c.success

    return users


def all_client_received(demand, room_id, t=None):

    rm = Room.objects.get(id=room_id)

    return Receipt.objects.filter(
        room_id=room_id, demand=demand.__name__, t=t, received=True).count() == rm.n_user


def create_room():

    if game.params.client.create_default_room():

        rm = create(parameters.default_room)

        return rm

    else:
        raise Exception("No room available. Auto room creation is disabled.")


def create(data):

    if Room.objects.filter(opened=True).first():
        raise Exception('Only ONE room can be opened at once.')

    t_max = int(data["t_max"])
    training_t_max = int(data["training_t_max"])

    count_type = [int(v) for k, v in data.items() if k.startswith("x")]
    n_user = sum(count_type)
    n_type = len(count_type)

    types = [i for i in range(n_type) for _ in range(count_type[i])]

    rm = Room(
        t_max=t_max,
        training_t_max=training_t_max,
        t=0,
        training_t=0,
        state=game.room.state.states.WELCOME,
        opened=True,
        n_user=n_user,
        n_type=n_type,
        types="/".join([str(i) for i in count_type])
    )

    rm.save()

    Choice.objects.bulk_create([
        Choice(
            room_id=rm.id,
            t=t,
            player_id=n,
            user_id=None,
            good_in_hand=types[n] if not t else None,
            desired_good=None,
            success=None,
        )
        for n in range(n_user) for t in range(t_max)
    ])

    TutorialChoice.objects.bulk_create([
        TutorialChoice(
            room_id=rm.id,
            t=t,
            player_id=n,
            user_id=None,
            good_in_hand=types[n] if not t else None,
            desired_good=None,
            success=None
        )
        for n in range(n_user) for t in range(training_t_max)
    ])

    for demand in ('init', 'survey', 'training_done'):

        Receipt.objects.bulk_create([
            Receipt(
                room_id=rm.id,
                player_id=n,
                demand=demand,
                t=None
            )
            for n in range(n_user)
        ])

        c = ConsumerTask(room_id=rm.id, demand=demand, t=None)
        c.save()

    for demand, t_maximum in zip(['training_choice', 'choice'], [training_t_max, t_max]):

        Receipt.objects.bulk_create([
            Receipt(
                room_id=rm.id,
                player_id=n,
                demand=demand,
                t=t
            )
            for n in range(n_user) for t in range(t_maximum)
        ])

    ConsumerTask.objects.bulk_create([
        ConsumerTask(
            room_id=rm.id,
            demand='choice',
            t=t
        ) for t in range(t_max)
    ])

    return rm


def get_progression(demand, rm, t, tuto=False):

    if demand == game.views.choice:

        return game.room.state.get_progress_for_choices(rm=rm, t=t, tuto=tuto)

    else:

        return game.user.state.get_progress_for_current_state(demand=demand, rm=rm)


def state_verification(u, rm, progress, t, demand, success=None):

    """

    Manage room and user states
    depending on demand made by client.

    """

    if demand == game.views.init:

        if u.state == game.room.state.states.WELCOME:

            u = game.user.state.set_state(
                        u=u,
                        state=game.room.state.states.SURVEY
            )

            wait = progress != 100

            if not wait:

                if rm.state == game.room.state.states.WELCOME:
                    game.room.state.set_state(
                        rm=rm,
                        state=game.room.state.states.SURVEY
                    )

        else:
            wait = _is_someone_in_the_current_state(
                rm=rm,
                state=game.room.state.states.WELCOME
            )

        return wait, u.state

    elif demand == game.views.survey:

        if u.state == game.room.state.states.SURVEY:

            u = game.user.state.set_state(
                u=u,
                state=game.room.state.states.TRAINING,
            )

            wait = progress != 100

            if not wait:

                if rm.state == game.room.state.states.SURVEY:
                    game.room.state.set_state(
                        rm=rm,
                        state=game.room.state.states.TRAINING
                    )

        else:
            wait = _is_someone_in_the_current_state(
                rm=rm,
                state=game.room.state.states.SURVEY
            )

        return wait, u.state

    elif demand == game.views.training_choice:

        t += 1
        wait = False
        end = t == rm.training_t_max

        return wait, t, end

    elif demand == game.views.training_done:

        if u.state == game.room.state.states.TRAINING:

            u = game.user.state.set_state(
                            u=u,
                            state=game.room.state.states.GAME,
            )

            wait = progress != 100

            if not wait:

                if rm.state == game.room.state.states.TRAINING:

                    game.room.state.set_state(
                        rm=rm,
                        state=game.room.state.states.GAME
                    )

        else:
            wait = _is_someone_in_the_current_state(
                rm=rm,
                state=game.room.state.states.TRAINING
            )

        return wait, u.state

    elif demand == game.views.choice:

        wait = progress != 100 or success == -2
        t += not wait

        end = t == rm.t_max

        if end:

            if rm.state == game.room.state.states.GAME:
                game.room.state.set_state(
                    rm=rm,
                    state=game.room.state.states.END
                )

            if u.state == game.room.state.states.GAME:
                u = game.user.state.set_state(
                    u=u,
                    state=game.room.state.states.END
                )
        else:

            game.room.state.set_rm_timestep(rm=rm, t=t, tuto=False)

        return u.state, wait, t, end


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


def _is_someone_in_the_current_state(state, rm):

    users = User.objects.filter(room_id=rm.id)

    if len(users) == rm.n_user:

        return state in [u.state for u in users]

    else:

        return True
