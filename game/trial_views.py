

def init(request):
    return {
        "wait": True,
        "progress": 50,
        "state": "survey",
        "choice_made": False,
        "tuto_choice_made": False,
        "score": 0,
        "good": 0,
        "tuto_good": 0,
        "desired_good": 1,
        "tuto_desired_good": 1,
        "t": 0,
        "t_max": 25,
        "tuto_t": 0,
        "tuto_t_max": 5,
        "pseudo": "Michel",
        "user_id": 0,
    }


def survey(request):
    return {
       "wait": False,
       "progress": 100,
    }


def tutorial_done(request):
    return {
        "wait": False,
        "progress": 100
    }


def tutorial_choice(request):
    return {
        "wait": False,
        "progress": 100,
        "success": True,
        "t": 1,
        "end": False,
        "score": 0,
    }


def choice(request):
    return {
        "wait": False,
        "progress": 100,
        "success": True,
        "t": 1,
        "end": False,
        "score": 0,
    }
