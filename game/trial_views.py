

def init(request):
    return {
        "wait": True,
        "progress": 50,
        "state": "survey",
        "choice_made": 0,
        "score": 0,
        "good": 0,
        "desired_good": 1,
        "t": 0,
        "pseudo": "Michel",
        "userId": 0
    }


def survey(request):
    return {
       "wait": 0,
       "progress": 100,
    }


def tutorial(request):
    return {
        "wait": 0,
        "progress": 100
    }


def choice(request):
    return {
        "wait": 0,
        "progress": 100,
        "success": 1,
        "t": 1,
    }
