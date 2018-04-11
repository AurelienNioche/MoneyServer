

def init(request):

    return {
        "wait": False,
        "progress": 50,
        "step": "tutorial",
        "choiceMade": False,
        "score": 0,
        "goodInHand": 0,
        "goodDesired": 1,
        "t": 0,
        "tMax": 25,
        "tutoGoodInHand": 0,
        "tutoGoodDesired": 1,
        "tutoChoiceMade": False,
        "tutoScore": 0,
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
        "tutoSuccess": True,
        "tutoT": 1,
        "tutoEnd": True,
        "tutoScore": 0,
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
