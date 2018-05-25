import threading

import game.room.client
import game.room.state
import game.consumers
import game.user.client
import game.consumer.state


def init(kwargs):

    while True:

        users = game.room.client.get_all_users_that_did_not_receive(room_id=kwargs['room_id'], demand=init)

        for user in users:

            if user.state == game.room.state.states.SURVEY:

                info = game.user.client.connect(
                    device_id=user.device_id,
                    skip_survey=kwargs['skip_survey'],
                    skip_training=kwargs['skip_training'],
                )[0]

                info.update({'wait': False, 'receipt': True})

                game.consumers.WSDialog.group_send(group=f'user-{user.id}', data=info)

        threading.Event().wait(1)
        stop_sending = game.room.client.all_client_received(room_id=kwargs['room_id'], demand=init)

        if stop_sending:
            break


def survey(kwargs):

    while True:

        users = game.room.client.get_all_users_that_did_not_receive(room_id=kwargs['room_id'], demand=survey)

        for user in users:

            game.consumers.WSDialog.group_send(
                group=f'user-{user.id}',
                data=kwargs['to_reply'],
            )

        threading.Event().wait(1)

        stop_sending = game.room.client.all_client_received(room_id=kwargs['room_id'], demand=survey)

        if stop_sending:
            break


def training_choice(kwargs):

    # User may have already received his response
    # because training choices results are directly send to
    # the client when he submits his choice
    stop_sending = game.user.client.user_received(
            room_id=kwargs['room_id'], player_id=kwargs['player_id'], demand=training_choice, t=kwargs['t'])

    # If he does not have confirmed he received
    while not stop_sending:

        game.consumers.WSDialog.group_send(
                group=f'user-{kwargs["user_id"]}',
                data=kwargs['to_reply'],
            )

        threading.Event().wait(1)

        stop_sending = game.user.client.user_received(
            room_id=kwargs['room_id'], player_id=kwargs['player_id'], demand=training_choice, t=kwargs['t'])

        if stop_sending:
            break


def training_done(kwargs):

    while True:

        users = game.room.client.get_all_users_that_did_not_receive(room_id=kwargs['room_id'], demand=training_done)

        for user in users:

            game.consumers.WSDialog.group_send(
                group=f'user-{user.id}',
                data=kwargs['to_reply'],
            )

        threading.Event().wait(1)

        stop_sending = game.room.client.all_client_received(room_id=kwargs['room_id'], demand=training_done)

        if stop_sending:
            break


def choice(kwargs):

    while True:

        # Get results for all users except the one asking
        users_that_did_not_receive = game.room.client.get_all_users_that_did_not_receive(
            room_id=kwargs['room_id'], demand=choice, t=kwargs['t']
        )

        results = game.room.client.get_results_for_all_users(room_id=kwargs['room_id'], t=kwargs['t'])

        users = [user for user in results
                 if user.id in [i.id for i in users_that_did_not_receive]]

        print('IN CHOIICE')
        for user_result in users:

            print(user_result)
            data = {
                'wait': False,
                'progress': kwargs['progress'],
                'success': user_result.success,
                'end': kwargs['end'],
                'score': user_result.score,
                't': kwargs['t'],
                'receipt': True,
                'demand': 'choice',
            }

            game.consumers.WSDialog.group_send(
                group=f'user-{user_result.id}', data=data,
            )

        threading.Event().wait(2)

        print()

        stop_sending = game.room.client.all_client_received(room_id=kwargs['room_id'], demand=choice, t=kwargs['t'])

        if stop_sending:
            break

