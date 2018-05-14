from collections import namedtuple

from utils import utils

from game.forms import ClientRequestForm

from dashboard.models import IntParameter

import game.trial_views
import game.user.client
import game.room.client
import game.params.client
import game.room.state
import game.consumers


def client_request(request):

    """
    main method taking request from client
    and returning
    :param request:
    :return: response
    """

    # Log
    utils.log("Websocket request: {}".format(list(request.items())), f=client_request)

    demand = request.get('demand')

    if not demand:
        raise Exception('"demand" key is required.')

    trial, skip_survey, skip_training = game.params.client.is_trial()

    if not trial:

        # Retrieve functions in current script
        functions = {
            f_name: f for f_name, f in globals().items()
            if not f_name.startswith("_")
        }

        # Retrieve demanded function from current script
        func = functions.get(demand)

        if not func:
            raise Exception("Bad demand.")

    else:

        try:
            # Get function from trial script
            func = getattr(game.trial_views, demand)
        except AttributeError:
            raise Exception("Bad demand.")

    args = _treat_args(
        request,
        {"skip_training": skip_training, "skip_survey": skip_survey}
    )

    to_reply = func(args)

    # utils.log("Post request: {}".format(list(to_reply.items())), f=client_request)

    to_reply['demand'] = demand
    to_reply['messageId'] = _increment_message_id()

    response = to_reply

    return response


def init(args):

    to_reply, u, rm = game.user.client.connect(
        device_id=args.device_id,
        skip_training=args.skip_training,
        skip_survey=args.skip_survey,
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=init,
    )

    to_reply.update({'wait': wait})
    to_reply.update({'progress': progress})

    if state != to_reply['step']:
        to_reply.update({'step': state})

    if wait:

        game.consumers.WSDialog.group_send(
            group=game.room.state.states.WELCOME,
            data={'wait': True, 'progress': progress}
        )

    else:

        users = game.room.client.get_all_users(rm=rm).exclude(id=u.id)

        for user in users:

            if user.state == game.room.state.states.SURVEY:

                info = game.user.client.connect(
                    device_id=user.device_id,
                    skip_survey=args.skip_survey,
                    skip_training=args.skip_training
                )[0]

                info.update({'wait': False})

                game.consumers.WSDialog.group_send(group=f'user-{user.id}', data=info)

    return to_reply


def survey(args):

    u = game.user.client.get_user(user_id=args.user_id)
    rm = game.room.client.get_room(room_id=u.room_id)

    game.user.client.submit_survey(
        u=u,
        gender=args.gender,
        age=args.age,
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=survey
    )

    game.consumers.WSDialog.group_send(
        group=game.room.state.states.SURVEY,
        data={'wait': wait, 'progress': progress}
    )

    to_reply = {
        "wait": wait,
        "progress": progress
    }

    return to_reply


def training_choice(args):

    u = game.user.client.get_user(user_id=args.user_id)
    rm = game.room.client.get_room(room_id=u.room_id)

    absolute_good = game.user.client.get_absolute_good(u=u, rm=rm, good=args.desired_good)

    success, score = game.user.client.submit_training_choice(
        u=u,
        rm=rm,
        desired_good=absolute_good,
        t=args.t
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t, tuto=True)

    wait, t, end = game.room.client.state_verification(
        rm=rm, u=u, t=args.t, progress=progress, demand=training_choice
    )

    to_reply = {
        "wait": wait,
        "trainingSuccess": success,
        "trainingScore": score,
        "trainingProgress": progress,
        "trainingT": args.t,
        "trainingEnd": end
    }

    return to_reply


def training_done(args):

    u = game.user.client.get_user(user_id=args.user_id)
    u = game.user.client.submit_training_done(u=u)

    rm = game.room.client.get_room(room_id=u.room_id)

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=training_done
    )

    game.consumers.WSDialog.group_send(
        group='training-done',
        data={'wait': wait, 'progress': progress}
    )

    to_reply = {
        "wait": wait,
        "progress": progress
    }

    return to_reply


def choice(args):

    u = game.user.client.get_user(user_id=args.user_id)
    rm = game.room.client.get_room(room_id=u.room_id)

    absolute_desired_good = game.user.client.get_absolute_good(u=u, good=args.desired_good, rm=rm)

    success, score = game.user.client.submit_choice(
        u=u,
        rm=rm,
        desired_good=absolute_desired_good,
        t=args.t
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    state, wait, t, end = game.room.client.state_verification(
        rm=rm, u=u, t=args.t, progress=progress, demand=choice, success=success
    )

    to_reply = {
        "wait": wait,
        "progress": progress,
        "success": success,
        "end": end,
        "score": score,
        "t": args.t,
    }

    if wait:

        game.consumers.WSDialog.group_send(
            group=f'game-t-{args.t}',
            data={'wait': True, 'progress': progress, 't': args.t}
        )

    else:

        # Get results for all users except the one asking
        users = game.room.client.get_results_for_all_users(rm=rm, t=args.t).exclude(id=u.id)

        for user_result in users:

                data = {
                    "wait": False,
                    "progress": progress,
                    "success": user_result.success,
                    "end": end,
                    "score": user_result.score,
                    "t": args.t,
                }

                game.consumers.WSDialog.group_send(
                    group=f'user-{user_result.id}', data=data
                )

    return to_reply


def _treat_args(request, options):

    form = ClientRequestForm(request)

    if form.is_valid():

        Args = namedtuple(
            "Args",
            ["demand", "device_id", "user_id",
             "age", "gender", "desired_good", "t", "skip_survey", "skip_training"]
        )

        args = Args(
            demand=form.cleaned_data.get("demand"),
            user_id=form.cleaned_data.get("userId"),
            device_id=form.cleaned_data.get("deviceId"),
            age=form.cleaned_data.get("age"),
            gender=form.cleaned_data.get("sex"),
            desired_good=form.cleaned_data.get("good"),
            t=form.cleaned_data.get("t"),
            skip_training=options["skip_training"],
            skip_survey=options["skip_survey"]
        )

        return args

    else:
        raise Exception('Error while treating request.')


def _set_headers(response):

    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Headers"] = "Accept, X-Access-Token, X-Application-Name, X-Request-Sent-Time"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Origin"] = "*"

    return response


def _increment_message_id():

    message_count = IntParameter.objects.filter(name="message_count").first()

    if not message_count:

        message_count = IntParameter(name="message_count", value=0, unit="int")

        message_count.save()

    message_count.value += 1

    message_count.save()

    return message_count.value





