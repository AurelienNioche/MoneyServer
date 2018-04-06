from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from utils import utils

from game.models import IntParameter, User, Choice
import game.trial_views


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
    trial = _is_trial()

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

        to_reply = func(request=request)

    except KeyError:
        raise Exception("Bad demand")

    response = JsonResponse(to_reply)
    response["Access-Control-Allow-Credentials"] = "true"
    response["Access-Control-Allow-Headers"] = "Accept, X-Access-Token, X-Application-Name, X-Request-Sent-Time"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Origin"] = "*"

    return response


def _is_trial():

    trial = IntParameter.objects.filter(name="trial").first()

    if not trial:

        trial = IntParameter(name="trial", value=1)
        trial.save()

    return trial.value
