from collections import namedtuple
from django.views.decorators.csrf import csrf_exempt
# from django.

from utils import utils

from game.forms import ClientRequestForm

import game.trial_views
import game.user.client
import game.room.client
import game.params.client
import game.room.state
import game.consumers


@csrf_exempt
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

    to_reply, consumer_info = func(args)

    if to_reply:
        to_reply['demand'] = demand
        consumer_info['demand'] = demand

    return to_reply, consumer_info


# def receipt_confirmation(args):
#
#     u = game.user.client.get_user(user_id=args.user_id)
#     rm = game.room.client.get_room(room_id=u.room_id)
#
#     game.user.client.set_all_precedent_receipt_confirmation_to_received(
#         u=u, t=args.t, demand=args.concerned_demand
#     )
#
#     game.user.client.receipt_confirmation(
#         rm=rm,
#         u=u,
#         t=args.t,
#         demand=args.concerned_demand
#     )
#
#     return None, None


def init(args):

    to_reply, u, rm = game.user.client.connect(
        device_id=args.device_id,
        skip_training=args.skip_training,
        skip_survey=args.skip_survey,
    )

    progress = game.room.client.get_progression(demand=init, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=init,
    )

    to_reply.update({'wait': wait})
    to_reply.update({'progress': progress})

    if state != to_reply['step']:
        to_reply.update({'step': state})

    consumer_info = {
        'room_id': rm.id,
        'skip_survey': args.skip_survey,
        'skip_training': args.skip_training,
        'user_id': u.id,
        'demand': args.demand,
        't': args.t
    }

    return to_reply, consumer_info


def survey(args):

    u = game.user.client.get_user(user_id=args.user_id)
    rm = game.room.client.get_room(room_id=u.room_id)

    game.user.client.submit_survey(
        u=u,
        gender=args.gender,
        age=args.age,
    )

    progress = game.room.client.get_progression(demand=survey, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=survey
    )

    to_reply = {
        "wait": wait,
        "progress": progress,
        "demand": args.demand
    }

    consumer_info = {
        'room_id': rm.id,
        'to_reply': to_reply,
        'user_id': u.id,
        'demand': args.demand
    }

    return to_reply, consumer_info


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

    progress = game.room.client.get_progression(demand=training_choice, rm=rm, t=args.t, tuto=True)

    wait, t, end = game.room.client.state_verification(
        rm=rm, u=u, t=args.t, progress=progress, demand=training_choice
    )

    to_reply = {
        "wait": wait,  # Wait is always false here
        "trainingSuccess": success,
        "trainingScore": score,
        "trainingProgress": progress,
        "t": args.t,
        "trainingEnd": end,
        "demand": args.demand
    }

    consumer_info = {
        "room_id": rm.id,
        "player_id": u.player_id,
        "user_id": u.id,
        "demand": args.demand,
        "to_reply": to_reply,
        "t": args.t
    }

    return to_reply, consumer_info


def training_done(args):

    u = game.user.client.get_user(user_id=args.user_id)
    u = game.user.client.submit_training_done(u=u)

    rm = game.room.client.get_room(room_id=u.room_id)

    progress = game.room.client.get_progression(demand=training_done, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=training_done
    )

    to_reply = {
        "wait": wait,
        "progress": progress,
        'demand': args.demand,
    }

    consumer_info = {
        "room_id": rm.id,
        "to_reply": to_reply,
        "demand": args.demand,
        "user_id": u.id,
    }

    return to_reply, consumer_info


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

    progress = game.room.client.get_progression(demand=choice, rm=rm, t=args.t)

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
        "demand": args.demand
    }

    consumer_info = {
        "progress": progress,
        "end": end,
        "t": args.t,
        "room_id": rm.id,
        "user_id": u.id,
        "demand": args.demand
    }

    return to_reply, consumer_info


def _treat_args(request, options):

    form = ClientRequestForm(request)

    if form.is_valid():

        Args = namedtuple(
            "Args",
            ["demand", "device_id", "user_id",
             "age", "gender", "desired_good",
             "t", "skip_survey", "skip_training",
             "concerned_demand"
             ]
        )

        args = Args(
            demand=form.cleaned_data.get("demand"),
            user_id=form.cleaned_data.get("userId"),
            device_id=form.cleaned_data.get("deviceId"),
            age=form.cleaned_data.get("age"),
            gender=form.cleaned_data.get("sex"),
            desired_good=form.cleaned_data.get("good"),
            t=form.cleaned_data.get("t"),
            concerned_demand=form.cleaned_data.get("concernedDemand"),
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
