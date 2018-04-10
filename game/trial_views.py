

def init(request):
    return {
        "wait": False,
        "progress": 50,
        "step": "survey",
        "choiceMade": False,
        "tutoChoiceMade": False,
        "score": 0,
        "good": 0,
        "tutoGood": 0,
        "desiredGood": 1,
        "tutoDesiredGood": 1,
        "t": 0,
        "tMax": 25,
        "tutoT": 0,
        "tutoTMax": 5,
        "pseudo": "Méchel",
        "userId": 0,
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
