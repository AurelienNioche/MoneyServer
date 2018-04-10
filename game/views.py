from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from collections import namedtuple

from utils import utils

from game.models import BoolParameter
import game.trial_views

import game.user.client
import game.room.client
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
    trial, skip_survey, skip_tutorial = _is_trial()

    try:

        if not trial:

            # Retrieve functions in current script
            functions = {
                f_name: f for f_name, f in globals().items()
                if not f_name.startswith("_")
            }

            # Retrieve demanded function
            func = functions[demand]

        else:

            # Get function from trial script
            func = getattr(game.trial_views, demand)

        args = _treat_args(request)

        to_reply = func(args)

    except (KeyError, AttributeError):
        raise Exception("Bad demand")

    to_reply["demand"] = demand
    to_reply["skip_tutorial"] = skip_tutorial
    to_reply["skip_survey"] = skip_survey

    response = JsonResponse(to_reply)

    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Headers"] = "Accept, X-Access-Token, X-Application-Name, X-Request-Sent-Time"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Origin"] = "*"

    return response


def _treat_args(request):

    Args = namedtuple(
        "Args",
        ["device_id", "user_id", "progress", "age", "gender", "desired_good", "t"]
    )

    args = Args(
        user_id=request.POST.get("user_id"),
        device_id=request.POST.get("device_id"),
        progress=request.POST.get("progress"),
        age=request.POST.get("age"),
        gender=request.POST.get("gender"),
        desired_good=request.POST.get("desired_good"),
        t=request.POST.get("t")
    )

    return args


def _is_trial():

    with transaction.atomic():

        trial = BoolParameter.objects.filter(name="trial").first()
        skip_survey = BoolParameter.objects.filter(name="skip_survey").first()
        skip_tutorial = BoolParameter.objects.filter(name="skip_tutorial").first()

        if not trial:

            trial = BoolParameter(name="trial", value=True)
            trial.save()

        if not skip_survey:

            skip_survey = BoolParameter(name="skip_survey", value=True)
            skip_survey.save()

        if not skip_tutorial:

            skip_tutorial = BoolParameter(name="skip_tutorial", value=True)
            skip_tutorial.save()

        return trial.value, skip_survey.value, skip_tutorial.value


def init(args):

    info = game.user.client.connect(device_id=args.device_id)

    to_reply = {
        "wait": info["wait"],
        "progress": info["progress"],
        "state": info["state"],
        "choice_made": info["choice_made"],
        "score": info["score"],
        "good": info["good_in_hand"],
        "desired_good": info["desired_good"],
        "t": info["t"],
        "user_id": info["user_id"],
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
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=utils.fname())

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
    wait, choice_progress, t, end = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=utils.fname())

    to_reply = {
        "wait": wait,
        "success": success,
        "score": score,
        "progress": choice_progress,
        "t": t,
        "end": end
    }

    return to_reply


def tutorial_done(args):

    game.user.client.submit_tutorial_done(user_id=args.user_id)

    wait, progress, = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=utils.fname())

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

    wait, choice_progress, t, end = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t, user_demand=utils.fname())

    to_reply = {
        "wait": wait,
        "progress": choice_progress,
        "success": success,
        "end": end,
        "score": score,
        "t": t
    }

    return to_reply

