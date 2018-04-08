from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from collections import namedtuple

from utils import utils

from game.models import IntParameter
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

    except KeyError:
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
        ["device_id", "user_id", "progress", "age", "gender", "choice", "t"]
    )

    args = Args(
        user_id=request.POST.get("user_id"),
        device_id=request.POST.get("device_id"),
        progress=request.POST.get("progress"),
        age=request.POST.get("age"),
        gender=request.POST.get("gender"),
        choice=request.POST.get("choice"),
        t=request.POST.get("t")
    )

    return args


def _is_trial():

    trial = IntParameter.objects.filter(name="trial").first()
    skip_survey = IntParameter.objects.filter(name="skip_survey").first()
    skip_tutorial = IntParameter.objects.filter(name="skip_tutorial").first()

    if not trial:

        trial = IntParameter(name="trial", value=1)
        trial.save()

    if not skip_survey:

        skip_survey = IntParameter(name="skip_survey", value=1)
        skip_survey.save()

    if not skip_tutorial:

        skip_tutorial = IntParameter(name="skip_tutorial", value=1)
        skip_tutorial.save()

    return trial.value, skip_survey.value, skip_tutorial.value


def init(args):

    info = game.user.client.connect(device_id=args.device_id)

    to_reply = {
        "wait": info[0],
        "progress": info[1],
        "state": info[2],
        "made_choice": info[3],
        "score": info[4],
        "good": info[5],
        "desired_good": info[6],
        "t": info[6],
        "pseudo": info[7],
        "user_id": info[8],
    }

    return to_reply


def survey(args):

    game.user.client.submit_survey(
        user_id=args.user_id,
        gender=args.gender,
        age=args.age,
    )

    has_to_wait, progress = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t)

    to_reply = {
        "wait": has_to_wait,
        "progress": progress
    }

    return to_reply


def choice(args):

    success = game.room.client.submit_choice(
        user_id=args.user_id,
        desired_good=args.choice,
        t=args.t
    )

    has_to_wait, progress, choice_progress = \
        game.room.client.get_progression(user_id=args.user_id, t=args.t)

    to_reply = {
        "wait": has_to_wait,
        "progress": progress,
        "choice_progress": choice_progress,
        "success": success
    }

    return to_reply

