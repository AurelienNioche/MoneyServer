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

    args = _treat_args(
        request,
        {"skip_tutorial": skip_tutorial, "skip_survey": skip_survey}
    )

    to_reply = func(args)

    utils.log("Post request: {}".format(list(to_reply.items())), f=client_request)

    to_reply["demand"] = demand
    to_reply["skipSurvey"] = skip_survey
    to_reply["skipTutorial"] = skip_tutorial

    response = JsonResponse(to_reply)

    return _set_headers(response)


def init(args):

    info, u, rm = game.user.client.connect(
        device_id=args.device_id,
        skip_tutorial=args.skip_tutorial,
        skip_survey=args.skip_survey,
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=init,
    )

    to_reply = {

        "wait": wait if u.state in ("welcome", ) else False,
        "progress": progress,

        "step": state,
        "score": info["score"],

        "t": info["t"],
        "tMax": info["t_max"],

        "choiceMade": info["choice_made"],
        "goodInHand": info["good_in_hand"],
        "goodDesired": info["desired_good"],

        "userId": info["user_id"],
        "pseudo": info["pseudo"],

        "tutoGoodInHand": info["tuto_good_in_hand"],
        "tutoChoiceMade": info["tuto_choice_made"],
        "tutoGoodDesired": info["tuto_desired_good"],
        "tutoT": info["tuto_t"],
        "tutoTMax": info["tuto_t_max"],
        "tutoScore": info["tuto_score"]
    }

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

    to_reply = {
        "wait": wait if state in ("survey", ) else False,
        "progress": progress
    }

    return to_reply


def tutorial_choice(args):

    u = game.user.client.get_user(user_id=args.user_id)
    rm = game.room.client.get_room(room_id=u.room_id)

    success, score = game.user.client.submit_tutorial_choice(
        u=u,
        rm=rm,
        desired_good=args.desired_good,
        t=args.t
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t, tuto=True)

    wait, t, end = game.room.client.state_verification(
        rm=rm, u=u, t=args.t, progress=progress, demand=tutorial_choice
    )

    to_reply = {
        "wait": wait,
        "tutoSuccess": success,
        "tutoScore": score,
        "tutoProgress": progress,
        "tutoT": t,
        "tutoEnd": end
    }

    return to_reply


def tutorial_done(args):

    u = game.user.client.get_user(user_id=args.user_id)
    u = game.user.client.submit_tutorial_done(u=u)

    rm = game.room.client.get_room(room_id=u.room_id)

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    wait, state = game.room.client.state_verification(
        u=u, rm=rm, t=args.t, progress=progress, demand=tutorial_done
    )

    to_reply = {
        "wait": wait if state in ("tutorial", ) else False,
        "progress": progress
    }

    return to_reply


def choice(args):

    u = game.user.client.get_user(user_id=args.user_id)
    rm = game.room.client.get_room(room_id=u.room_id)

    success, score = game.user.client.submit_choice(
        u=u,
        rm=rm,
        desired_good=args.desired_good,
        t=args.t
    )

    progress = game.room.client.get_progression(u=u, rm=rm, t=args.t)

    wait, t, end = game.room.client.state_verification(
        rm=rm, u=u, t=args.t, progress=progress, demand=choice
    )

    to_reply = {
        "wait": wait if success is not None else True,
        "progress": progress,
        "success": success,
        "end": end,
        "score": score,
        "t": t
    }

    return to_reply


def _treat_args(request, options):

    form = ClientRequestForm(request.POST)

    if form.is_valid():

        Args = namedtuple(
            "Args",
            ["demand", "device_id", "user_id",
             "age", "gender", "desired_good", "t", "skip_survey", "skip_tutorial"]
        )

        args = Args(
            demand=form.cleaned_data.get("demand"),
            user_id=form.cleaned_data.get("user_id"),
            device_id=form.cleaned_data.get("device_id"),
            age=form.cleaned_data.get("age"),
            gender=form.cleaned_data.get("sex"),
            desired_good=form.cleaned_data.get("good"),
            t=form.cleaned_data.get("t"),
            skip_tutorial=options["skip_tutorial"],
            skip_survey=options["skip_survey"]
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

