import requests
import json
import multiprocessing as ml
import time


# --------------- Init ----------------- #

class KeyInit:
    demand = "demand"
    device_id = "device_id"

# -------------- Survey ----------------- #


class KeySurvey:
    demand = "demand"
    user_id = "user_id"
    age = "age"
    gender = "gender"
    t = "t"

# -------------- tuto ----------------- #


class KeyTuto:
    demand = "demand"
    user_id = "user_id"
    progress = "progress"

# -------------- Play -------------------- #


class KeyChoice:
    demand = "demand"
    choice = "choice"
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

        self.game_state = "welcome"

    def _request(self, data):

        try:

            r = requests.post(self.url, data=data)
            args = json.loads(r.text)

            # return execution of reply function with response
            func = getattr(self, "reply_" + args["demand"])
            return func(args)

        except Exception as e:
            print("Error while treating request: {}".format(e))

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

        self.user_id = args["user_id"]
        self.good_in_hand = args["good"]
        self.desired_good = args["desired_good"] if args["desired_good"] else 1
        self.t = args["t"]
        self.choice_made = args["choice_made"]
        self.tuto_t = args["tuto_t"]
        self.tuto_good = args["tuto_good"]
        self.tuto_desired_good = args["tuto_desired_good"]
        self.tuto_t_max = args["tuto_t_max"]
        self.game_state = args["state"]

        return True, args["wait"]

    def survey(self):

        return self._request({
            KeySurvey.demand: "survey",
            KeySurvey.age: 31,
            KeySurvey.gender: "female",
            KeySurvey.user_id: self.user_id,
            KeySurvey.t: self.t,
        })

    @print_reply
    def reply_survey(self, args):

        return True, args["wait"]

    # --------------------- tuto  ------------------------------------ #

    def tutorial(self):

        return self._request({
            KeyTuto.demand: "tutorial",
            KeyTuto.progress: 100,
            KeyTuto.user_id: self.user_id,
        })

    @print_reply
    def reply_tutorial(self, args):

        return True, args["wait"]

    # --------------------- choice ------------------------------------ #

    def choice(self):

        return self._request({
            KeyChoice.demand: "choice",
            KeyChoice.user_id: self.user_id,
            KeyChoice.choice: self.desired_good,
            KeyChoice.t: self.t
        })

    @print_reply
    def reply_choice(self, args):
        self._increment_time_step()
        return True, not args["end"]


class BotProcess(ml.Process):

    def __init__(self, url, start_event, delay=3, device_id="1"):
        super().__init__()
        self.start_event = start_event
        self.b = BotClient(url=url, device_id=device_id)
        self.delay = delay

    def _wait(self):

        ml.Event().wait(timeout=self.delay)

    def while_true(self, f, next_state):

        self._wait()

        r = f()

        if r and len(r) > 1:
            success, wait = r
        else:
            success, wait = False, True

        while not success or wait:
            self._wait()
            wait = f()

        if not self.b.state:
            self.b.state = next_state

    def init(self):

        self.while_true(f=self.b.init, next_state="survey")

    def survey(self):

        self.while_true(f=self.b.survey, next_state="tutorial")

    def tutorial(self):

        self.while_true(f=self.b.tutorial, next_state="game")

    def game(self):

        self.while_true(f=self.b.choice, next_state="end")

    def run(self):

        self.init()
        self.survey()
        self.tutorial()
        self.game()


def main():

    url = "http://127.0.0.1:8000/client_request/"

    n_accounts = 50

    start_event = ml.Event()

    for n in range(n_accounts):

        time.sleep(3)

        device_id = "bot{}".format(n)

        b = BotProcess(
            url=url,
            start_event=start_event,
            device_id=device_id
        )

        b.start()


if __name__ == "__main__":

    main()
