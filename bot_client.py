import requests
import json
import time
import numpy as np


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
    desired_good = "desired_good"
    t = "t"

# -------------- Play -------------------- #


class KeyChoice:
    demand = "demand"
    desired_good = "desired_good"
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
        self.tuto_t_max = None
        self.choice_made = None

        self.game_state = None

    def _request(self, data):

        try:

            r = requests.post(self.url, data=data)
            args = json.loads(r.text)

            # return execution of reply function with response
            func = getattr(self, "reply_" + args["demand"])
            return func(args)

        except Exception as e:
            print("Error while treating request: {}".format(e.with_traceback(e.__traceback__)))

    def _increment_time_step(self):
        self.t += 1

    # --------------------- Init ------------------------------------ #

    def init(self):

        return self._request({
            KeyInit.demand: "init",
            KeyInit.device_id: self.device_id,
        })

    @print_reply
    def reply_init(self, args):

        self.user_id = args["userId"]
        self.good_in_hand = args["good"]
        self.desired_good = args["desiredGood"] if args["desiredGood"] else 1
        self.t = args["t"]
        self.choice_made = args["choiceMade"]
        self.tuto_t = args["tutoT"]
        self.tuto_good = args["tutoGood"]
        self.tuto_desired_good = args["tutoDesiredGood"]
        self.tuto_t_max = args["tutoTMax"]
        self.game_state = args["state"]

        return True, args["wait"]

    def survey(self):

        return self._request({
            KeySurvey.demand: "survey",
            KeySurvey.age: 31,
            KeySurvey.sex: "female",
            KeySurvey.user_id: self.user_id,
        })

    @print_reply
    def reply_survey(self, args):

        return True, args["wait"]

    # --------------------- tuto  ------------------------------------ #

    def tutorial(self):

        return self._request({
            KeyTuto.demand: "tutorial_choice",
            KeyTuto.progress: 100,
            KeyTuto.user_id: self.user_id,
            KeyTuto.desired_good: np.random.randint(3),
            KeyTuto.t: self.tuto_t,
        })

    @print_reply
    def reply_tutorial_choice(self, args):

        self.tuto_t = args["tutoT"]

        return True, args["wait"], args["tutoEnd"]

    def tutorial_done(self):

        return self._request({
            "demand": "tutorial_done",
            "user_id": self.user_id
        })

    @print_reply
    def reply_tutorial_done(self, args):

        return True, args["wait"]

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
        self.t = args["t"]
        return True, args["wait"], args["end"]


class BotProcess:

    def __init__(self, url, delay=0.5, device_id="1"):
        super().__init__()
        self.b = BotClient(url=url, device_id=device_id)
        self.delay = delay

    def _wait(self):

        time.sleep(self.delay)

    def wait_for_a_response(self, f):

        self._wait()

        r = f()

        while not r:
            self._wait()
            r = f()

        return r[1:]

    def welcome(self):

        wait, = self.wait_for_a_response(f=self.b.init)
        while wait:
            wait, = self.wait_for_a_response(f=self.b.init)

    def survey(self):

        wait, = self.wait_for_a_response(f=self.b.survey)
        while wait:
            wait, = self.wait_for_a_response(f=self.b.survey)

    def tutorial(self):

        wait, end = self.wait_for_a_response(f=self.b.tutorial)
        while not end:
            print("Tutorial: t = {}".format(self.b.tuto_t))
            wait, end = self.wait_for_a_response(f=self.b.tutorial)

        wait, = self.wait_for_a_response(f=self.b.tutorial_done)
        while wait:
            wait, self.wait_for_a_response(f=self.b.tutorial_done)

    def game(self):

        wait, end = self.wait_for_a_response(f=self.b.choice)
        while not end:
            print("Game: t = {}".format(self.b.t))
            wait, end = self.wait_for_a_response(f=self.b.choice)

    def end(self):

        print("It is the end, my only friend, the end.")

    def run(self):

        input("Run? Press a key.")

        methods = iter([
            self.welcome,
            self.survey,
            self.tutorial,
            self.game,
            self.end
        ])

        mapping = {
            "welcome": self.welcome,
            "survey": self.survey,
            "tutorial": self.tutorial,
            "game": self.game,
            "end": self.end
        }

        self.welcome()

        next_method = mapping[self.b.game_state]

        while True:
            next_method()
            next_method = next(methods)

            if next_method.__name__ == "end":
                self.end()
                break

            # input("Go to state {}? Press a key.".format(next_method.__name__))


def main():

    url = "http://127.0.0.1:8000/client_request/"

    n = input("Bot id? > ")
    device_id = "bot{}".format(n)

    b = BotProcess(
        url=url,
        device_id=device_id
    )

    b.run()


if __name__ == "__main__":

    main()
