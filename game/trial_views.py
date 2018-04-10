

def init(request):
    return {
        "wait": True,
        "progress": 50,
        "state": "survey",
        "choice_made": 0,
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
       "wait": 0,
       "progress": 100,
    }


def tutorial_done(request):
    return {
        "wait": 0,
        "progress": 100
    }


def tutorial_choice(request):
    return {
        "wait": 0,
        "progress": 100,
        "success": 1,
        "t": 1,
    }


def choice(request):
    return {
        "wait": 0,
        "progress": 100,
        "success": 1,
        "t": 1,
    }
