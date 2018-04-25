import requests
import time
import numpy as np
import multiprocessing as ml
import argparse


# --------------- Init ----------------- #

class KeyInit:
    demand = "demand"
    device_id = "device_id"

# -------------- Survey ----------------- #


class KeySurvey:
    demand = "demand"
    user_id = "user_id"
    age = "age"
    sex = "sex"

# -------------- tuto ----------------- #


class KeyTuto:
    demand = "demand"
    user_id = "user_id"
    progress = "progress"
    desired_good = "good"
    t = "t"

# -------------- Play -------------------- #


class KeyChoice:
    demand = "demand"
    desired_good = "good"
    t = "t"
    user_id = "user_id"

# ----------------------------------------- #


def print_reply(f):
    def wrapper(obj, args):
        print("{} {}: {} \n".format(obj.device_id, f.__name__, args.items()))
        return f(obj, args)

    return wrapper


class BotClient:

    def __init__(self, url, device_id):

        self.url = url
        self.device_id = device_id

        self.t = None
        self.state = None
        self.user_id = None
        self.good_in_hand = None
        self.desired_good = None
        self.made_choice = None
        self.wait = None
        self.tuto_good = None
        self.tuto_t = None
        self.tuto_desired_good = None
        self.tuto_good_in_hand = None
        self.tuto_t_max = None
        self.choice_made = None
        self.n_good = None

        self.game_state = None

    def _request(self, data):

        while True:

            try:

                r = requests.post(self.url, data=data)
                args = r.json()

                # return execution of reply function with response
                func = getattr(self, "reply_" + args["demand"])
                return func(args)

            except Exception as e:
                print("Error while treating request: {}".format(e))
                continue

    def get_desired_good(self, tuto=False):

        desired_good = np.random.randint(self.n_good)

        if tuto:
            while desired_good == self.tuto_good_in_hand:
                desired_good = np.random.randint(self.n_good)
        else:
            while desired_good == self.good_in_hand:
                desired_good = np.random.randint(self.n_good)

        return desired_good

    # --------------------- Init ------------------------------------ #

    def init(self):

        return self._request({
            KeyInit.demand: "init",
            KeyInit.device_id: self.device_id,
        })

    @print_reply
    def reply_init(self, args):

        self.user_id = args["userId"]
        self.good_in_hand = args["goodInHand"]

        self.n_good = args["nGood"]

        if args["goodDesired"]:
            self.desired_good = args["goodDesired"]

        else:
            self.desired_good = self.get_desired_good()

        if args["tutoGoodDesired"]:
            self.tuto_desired_good = args["tutoGoodDesired"]

        else:
            self.tuto_desired_good = self.get_desired_good(tuto=True)

        self.t = args["t"]
        self.choice_made = args["choiceMade"]
        self.tuto_t = args["tutoT"]
        self.tuto_good = args["tutoGoodInHand"]
        self.tuto_t_max = args["tutoTMax"]

        self.game_state = args["step"] + "_choice" if args["step"] == 'tutorial' else args["step"]

        if args["skipSurvey"]:
            self.game_state = "tutorial_choice"
        if args["skipTutorial"]:
            self.game_state = "game"

        return args["wait"]

    def survey(self):

        return self._request({
            KeySurvey.demand: "survey",
            KeySurvey.age: 31,
            KeySurvey.sex: "female",
            KeySurvey.user_id: self.user_id,
        })

    @print_reply
    def reply_survey(self, args):

        return args["wait"]

    # --------------------- tuto  ------------------------------------ #

    def tutorial(self):

        return self._request({
            KeyTuto.demand: "tutorial_choice",
            KeyTuto.progress: 100,
            KeyTuto.user_id: self.user_id,
            KeyTuto.desired_good: self.tuto_desired_good,
            KeyTuto.t: self.tuto_t,
        })

    @print_reply
    def reply_tutorial_choice(self, args):

        if not args["wait"]:

            if args["tutoSuccess"] is not None:

                if args["tutoSuccess"]:

                    if self.tuto_desired_good == 1:
                        self.tuto_good_in_hand = 0
                    else:
                        self.tuto_good_in_hand = self.tuto_desired_good

                self.tuto_t = args["tutoT"]

                self.tuto_desired_good = self.get_desired_good(tuto=True)

            else:
                raise Exception("Do not wait but success is None")

        return args["wait"], args["tutoEnd"]

    def tutorial_done(self):

        return self._request({
            "demand": "tutorial_done",
            "user_id": self.user_id
        })

    @print_reply
    def reply_tutorial_done(self, args):

        return args["wait"]

    # --------------------- choice ------------------------------------ #

    def choice(self):

        return self._request({
            KeyChoice.demand: "choice",
            KeyChoice.user_id: self.user_id,
            KeyChoice.desired_good: self.desired_good,
            KeyChoice.t: self.t
        })

    @print_reply
    def reply_choice(self, args):

        if not args["wait"]:

            if args["success"] is not None:

                if args["success"]:

                    if self.desired_good == 1:
                        self.good_in_hand = 0
                    else:
                        self.good_in_hand = self.desired_good

                self.t = args["t"]

                self.desired_good = self.get_desired_good()

            else:
                raise Exception("Do not wait but success is None")

        return args["wait"], args["end"]


def bot_factory(base, device_id, delay, url, wait_event, seed):

    class BotProcess(base):

        def __init__(self):

            super().__init__()

            self.b = BotClient(url=url, device_id=device_id)
            self.delay = delay
            self.ml = isinstance(self, ml.Process)

        def _wait(self):

            wait_event(self.delay)

        def welcome(self):

            wait = self.b.init()
            while wait:
                wait = self.b.init()

        def survey(self):

            wait = self.b.survey()
            while wait:
                wait = self.b.survey()

        def tutorial_choice(self):

            wait, end = self.b.tutorial()
            while not end:
                print("Tutorial: t = {}".format(self.b.tuto_t))
                wait, end = self.b.tutorial()

        def tutorial_done(self):

            wait = self.b.tutorial_done()
            while wait:
                wait = self.b.tutorial_done()

        def game(self):

            wait, end = self.b.choice()
            while not end:
                print("Game: t = {}".format(self.b.t))
                wait, end = self.b.choice()

        @staticmethod
        def end():

            print("It is the end, my only friend, the end.")

        def run(self):

            np.random.seed(seed)

            if not self.ml:
                input("Run? Press a key.")

            methods = [
                self.welcome,
                self.survey,
                self.tutorial_choice,
                self.tutorial_done,
                self.game,
                self.end
            ]

            mapping = {
                "welcome": self.welcome,
                "survey": self.survey,
                "tutorial_choice": self.tutorial_choice,
                "tutorial_done": self.tutorial_done,
                "game": self.game,
                "end": self.end
            }

            self.welcome()

            next_method = mapping[self.b.game_state]
            idx = methods.index(next_method)

            if not self.ml:
                input("Go to state {}? Press a key.".format(next_method.__name__))

            while True:
                next_method()
                idx += 1
                next_method = methods[idx]

                if next_method.__name__ == "end":
                    self.end()
                    break

            if not self.ml:
                input("Go to state {}? Press a key.".format(next_method.__name__))

    return BotProcess()


def main(args):

    # url = "http://money.getz.fr/client_request/"
    url = "http://127.0.0.1:8000/client_request/"

    if not args.number:

        n = input("Bot id? > ")
        device_id = "bot{}".format(n)

        b = bot_factory(
            base=object,
            wait_event=time.sleep,
            url=url,
            device_id=device_id,
            delay=2,
            seed=1
        )

        b.run()

    else:

        n = int(args.number)

        for b in range(n):

            device_id = "bot{}".format(b)

            bot = bot_factory(
                base=ml.Process,
                wait_event=ml.Event().wait,
                url=url,
                device_id=device_id,
                delay=3,
                seed=b,
            )

            bot.start()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run bots.')

    parser.add_argument('-n', '--number', action="store", default=None,
                        help="number of bots")

    parsed_args = parser.parse_args()

    main(parsed_args)
