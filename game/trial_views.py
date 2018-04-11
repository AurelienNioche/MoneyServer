

def init(request):

    return {
        "userId": 0,
        "pseudo": "Méchel",

        "wait": False,
        "progress": 50,

        "step": "tutorial",

        "tutoT": 0,
        "tutoTMax": 5,
        "tutoGoodInHand": 0,
        "tutoGoodDesired": 1,
        "tutoChoiceMade": False,
        "tutoScore": 0,

        "t": 0,
        "tMax": 25,
        "goodInHand": 0,
        "goodDesired": 1,
        "choiceMade": False,
        "score": 0,

        "skipSurvey": False,
        "skipTutorial": False,
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
        "tutoScore": 0,
        "tutoEnd": True,
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
