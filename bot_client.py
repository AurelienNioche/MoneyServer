import requests
import time
import threading
import numpy as np
import multiprocessing as ml
import argparse
import json

import websocket
websocket.enableTrace(True)


# --------------- Init ----------------- #

class KeyInit:
    demand = "demand"
    device_id = "deviceId"

# -------------- Survey ----------------- #


class KeySurvey:
    demand = "demand"
    user_id = "userId"
    age = "age"
    sex = "sex"

# -------------- tuto ----------------- #


class KeyTuto:
    demand = "demand"
    user_id = "userId"
    progress = "progress"
    desired_good = "good"
    t = "t"

# -------------- Play -------------------- #


class KeyChoice:
    demand = "demand"
    desired_good = "good"
    t = "t"
    user_id = "userId"

# ----------------------------------------- #


# def print_reply(f):
#     def wrapper(obj, args):
#         print("{} {}: {} \n".format(obj.device_id, f.__name__, args.items()))
#         return f(obj, args)
#
#     return wrapper


class BotClient:

    def __init__(self, url, device_id):

        self.ws = None
        self._connect(url)

        self.url = url

        self.device_id = device_id

        self.t = None
        self.state = None
        self.user_id = None
        self.good_in_hand = None
        self.desired_good = None
        self.made_choice = None
        self.wait = None
        self.training_good = None
        self.training_t = None
        self.training_desired_good = None
        self.training_good_in_hand = None
        self.training_t_max = None
        self.choice_made = None
        self.n_good = None

        self.game_state = None

        self.training_end = None
        self.game_end = None

        self.wait_for_server = None

    def _connect(self, url):

        self.ws = websocket.WebSocketApp(
            url=url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open

        self.t = threading.Thread(target=self.ws.run_forever)
        self.t.daemon = True
        self.t.start()

    def _request(self, data):

        print("sending ", data)
        self.ws.send(json.dumps(data))

    def on_open(self, *args):

        print('Connection established')

    def on_error(self, message):

        print(message)
        self._connect(url=self.url)

    def on_close(self, message):

        print("websocket is closed.")
        self._connect(self.url)

    def on_message(self, ws, args):

        data = json.loads(args)

        if data.get('group-send'):
            for _ in range(100):
                print('IT IS A GROUP SEND')

        if isinstance(data, dict):
            # return execution of reply function with response
            if 'demand' in data:
                func = getattr(self, "reply_" + data["demand"])
                func(data)
            else:
                self.wait_for_server = data['wait']
        else:
            print(data)

    def get_desired_good(self, training=False):

        desired_good = np.random.randint(self.n_good)

        if training:
            while desired_good == self.training_good_in_hand:
                desired_good = np.random.randint(self.n_good)
        else:
            while desired_good == self.good_in_hand:
                desired_good = np.random.randint(self.n_good)

        return desired_good

    # --------------------- Init ------------------------------------ #

    def init(self):

        self._request({
            KeyInit.demand: "init",
            KeyInit.device_id: self.device_id,
        })

    def reply_init(self, args):

        self.user_id = args["userId"]

        self.good_in_hand = args["goodInHand"]

        self.n_good = args["nGood"]

        if args["goodDesired"]:
            self.desired_good = args["goodDesired"]

        else:
            self.desired_good = self.get_desired_good()

        if args["trainingGoodDesired"]:
            self.training_desired_good = args["trainingGoodDesired"]

        else:
            self.training_desired_good = self.get_desired_good(training=True)

        self.t = args["t"]
        self.choice_made = args["choiceMade"]
        self.training_t = args["trainingT"]
        self.training_good_in_hand = args["trainingGoodInHand"]
        assert self.training_good_in_hand == 0
        self.training_t_max = args["trainingTMax"]

        self.game_state = args["step"] + "_choice" if args["step"] == 'tutorial' else args["step"]

        if args["skipSurvey"]:
            self.game_state = "tutorial_choice"
        if args["skipTutorial"]:
            self.game_state = "game"

        self.wait_for_server = args['wait']

    def survey(self):

        self._request({
            KeySurvey.demand: "survey",
            KeySurvey.age: 31,
            KeySurvey.sex: "female",
            KeySurvey.user_id: self.user_id,
        })

    def reply_survey(self, args):

        self.wait_for_server = args['wait']

    # --------------------- tuto  ------------------------------------ #

    def tutorial(self):

        self._request({
            KeyTuto.demand: "tutorial_choice",
            KeyTuto.progress: 100,
            KeyTuto.user_id: self.user_id,
            KeyTuto.desired_good: self.training_desired_good,
            KeyTuto.t: self.training_t,
        })

    def reply_tutorial_choice(self, args):

        if not args["wait"]:

            if args["trainingSuccess"] is not None:

                if args["trainingSuccess"]:

                    if self.training_desired_good == 1:
                        self.training_good_in_hand = 0
                    else:
                        self.training_good_in_hand = self.training_desired_good

                self.training_t = args["trainingT"]

                self.training_desired_good = self.get_desired_good(training=True)

            else:
                raise Exception("Do not wait but success is None")

        self.training_end = args['trainingEnd']
        self.wait_for_server = args['wait']

    def tutorial_done(self):

        self._request({
            "demand": "tutorial_done",
            "user_id": self.user_id
        })

    def reply_tutorial_done(self, args):

        self.wait_for_server = args['wait']

    # --------------------- choice ------------------------------------ #

    def choice(self):

        self._request({
            KeyChoice.demand: "choice",
            KeyChoice.user_id: self.user_id,
            KeyChoice.desired_good: self.desired_good,
            KeyChoice.t: self.t
        })

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

        self.game_end = args['end']
        self.wait_for_server = args['wait']


def bot_factory(base, device_id, delay, url, wait_event, seed):

    class BotProcess(base):

        def __init__(self):

            super().__init__()

            self.b = BotClient(url=url, device_id=device_id)
            self.delay = delay
            self.ml = isinstance(self, threading.Thread)
            self.wait_event = wait_event

        def wait(self):

            self.wait_event(self.delay)

        def welcome(self):

            self.b.init()

            while self.b.wait_for_server is None:
                self.wait()

            while self.b.wait_for_server:
                self.wait()

        def survey(self):

            self.b.survey()

            while self.b.wait_for_server:
                self.wait()

        def tutorial_choice(self):

            while not self.b.training_end:
                self.b.tutorial()

                print("Tutorial: t = {}".format(self.b.training_t))

                while self.b.wait_for_server:
                    self.wait()

        def tutorial_done(self):

            self.b.tutorial_done()

            while self.b.wait_for_server:
                self.wait()

        def game(self):

            while not self.b.game_end:
                self.b.choice()

                print("Tutorial: t = {}".format(self.b.t))

                while self.b.wait_for_server:
                    self.wait()

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

            print("Game state is:", self.b.game_state)

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
    # url = "http://127.0.0.1:8000/client_request/"
    url = 'ws://localhost:8000/'

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
                base=threading.Thread,
                wait_event=ml.Event().wait,
                url=url,
                device_id=device_id,
                delay=0.5,
                seed=b,
            )

            bot.start()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run bots.')

    parser.add_argument('-n', '--number', action="store", default=None,
                        help="number of bots")

    parsed_args = parser.parse_args()

    main(parsed_args)


