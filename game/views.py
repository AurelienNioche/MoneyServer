from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from collections import namedtuple

from utils import utils

from game.forms import ClientRequestForm

import game.trial_views
import game.user.client
import game.room.client
import game.params.client
import game.room.state


@csrf_exempt
def client_request(request):

    """
    main method taking request from client
    and returning
    :param request:
    :return: response
    """

    # Log
    utils.log("Post request: {}".format(list(request.POST.items())), f=client_request)

    demand = request.POST["demand"]
    trial, skip_survey, skip_tutorial = game.params.client.is_trial()

    if not trial:

        # Retrieve functions in current script
        functions = {
            f_name: f for f_name, f in globals().items()
            if not f_name.startswith("_")
        }

        try:
            # Retrieve demanded function from current script
            func = functions[demand]
        except KeyError:
            raise Exception("Bad demand.")

    else:

        try:
            # Get function from trial script
            func = getattr(game.trial_views, demand)
        except AttributeError:
            raise Exception("Bad demand.")

    args = _treat_args(request)

    to_reply = func(args)

    to_reply["demand"] = demand
    to_reply["skip_tutorial"] = skip_tutorial
    to_reply["skip_survey"] = skip_survey

    response = JsonResponse(to_reply)

    return _set_headers(response)


def init(args):

    info = game.user.client.connect(device_id=args.device_id)

    to_reply = {
        "wait": info["wait"],
        "progress": info["progress"],
        "state": info["state"],
        "choiceMade": info["choice_made"],
        "tutoChoiceMade": info["tuto_choice_made"],
        "score": info["score"],
        "good": info["good_in_hand"],
        "tutoGood": info["tuto_good_in_hand"],
        "desiredGood": info["desired_good"],
        "tutoDesiredGood": info["tuto_desired_good"],
        "t": info["t"],
        "tMax": info["t_max"],
        "tutoT": info["tuto_t"],
        "tutoTMax": info["tuto_t_max"],
        "userId": info["user_id"],
        "pseudo": info["pseudo"],
    }

    return to_reply


def survey(args):

    game.user.client.submit_survey(
        user_id=args.user_id,
        gender=args.gender,
        age=args.age,
    )

    wait, progress,  = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=args.demand)

    to_reply = {
        "wait": wait,
        "progress": progress
    }

    return to_reply


def tutorial_choice(args):

    success, score = game.user.client.submit_tutorial_choice(
        user_id=args.user_id,
        desired_good=args.desired_good,
        t=args.t
    )

    rm, choice_progress = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, tuto=True)

    wait, t, end = game.room.client.state_verification(rm=rm, t=args.t)

    to_reply = {
        "wait": wait,
        "tutoSuccess": success,
        "tutoScore": score,
        "tutoProgress": choice_progress,
        "tutoT": t,
        "tutoEnd": end
    }

    return to_reply


def tutorial_done(args):

    game.user.client.submit_tutorial_done(user_id=args.user_id)

    wait, progress, = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=args.demand)

    to_reply = {
        "wait": wait,
        "progress": progress
    }

    return to_reply


def choice(args):

    success, score = game.room.client.submit_choice(
        user_id=args.user_id,
        desired_good=args.desired_good,
        t=args.t
    )

    wait, choice_progress, end, t = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=args.demand)

    to_reply = {
        "wait": wait,
        "progress": choice_progress,
        "success": success,
        "end": end,
        "score": score,
        "t": t
    }

    return to_reply


def _treat_args(request):

    form = ClientRequestForm(request.POST)

    if form.is_valid():

        Args = namedtuple(
            "Args",
            ["demand", "device_id", "user_id", "age", "gender", "desired_good", "t"]
        )

        args = Args(
            demand=form.cleaned_data.get("demand"),
            user_id=form.cleaned_data.get("user_id"),
            device_id=form.cleaned_data.get("device_id"),
            age=form.cleaned_data.get("age"),
            gender=form.cleaned_data.get("sex"),
            desired_good=form.cleaned_data.get("desired_good"),
            t=form.cleaned_data.get("t")
        )

        return args

    else:
        raise Exception('Error while treating POST arguments.')


def _set_headers(response):

    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Headers"] = "Accept, X-Access-Token, X-Application-Name, X-Request-Sent-Time"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Origin"] = "*"

    return response

