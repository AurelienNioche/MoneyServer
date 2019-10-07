

def init(request):

    return {
        "userId": 0,
        "pseudo": "Méchel",

        "step": "training",

       "trainingT": 0,
       "trainingTMax": 5,
       "trainingGoodInHand": 0,
       "trainingGoodDesired": 1,
       "trainingScore": 0,
       "trainingChoiceMade": False,

       "t": 0,
       "tMax": 25,
       "goodInHand": 0,
       "goodDesired": 1,
       "score": 0,
       "choiceMade": False,

        "nGood": 3,

        "wait": False,
        "progress": 50,

        "skipSurvey": False,
        "skiptrainingrial": False,
    }, {}


def survey(request):
    return {
       "wait": False,
       "progress": 100,
    }, {}


def training_done(request):
    return {
        "wait": False,
        "progress": 100
    }, {}


def training_choice(request):
    return {
        "wait": False,
        "trainingScore": 0,
        "trainingSuccess": True,
        "trainingProgress": 100,
        "t": request.t,
        "trainingEnd": True,
    }, {}


def choice(request):
    return {
        "wait": False,
        "progress": 100,
        "success": True,
        "end": False,
        "score": 0,
        "t": request.t,
    }, {}
