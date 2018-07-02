from django.db import transaction

from game.models import BoolParameter, FloatParameter, IntParameter


def is_trial():

    with transaction.atomic():

        trial = BoolParameter.objects.filter(name="trial").first()
        skip_survey = BoolParameter.objects.filter(name="skip_survey").first()
        skip_training = BoolParameter.objects.filter(name="skip_training").first()

        if not trial:

            trial = BoolParameter(name="trial", value=False)
            trial.save()

        if not skip_survey:

            skip_survey = BoolParameter(name="skip_survey", value=True)
            skip_survey.save()

        if not skip_training:

            skip_training = BoolParameter(name="skip_training", value=True)
            skip_training.save()

        return trial.value, skip_survey.value, skip_training.value


def create_default_room():

    with transaction.atomic():

        auto_room = BoolParameter.objects.filter(name="auto_room").first()

        if not auto_room:

            auto_room = BoolParameter(name="auto_room", value=True)
            auto_room.save()

        return auto_room.value


def get_ping_frequency():

    ping = FloatParameter.objects.filter(name="ping").first()

    if not ping:

        ping = FloatParameter(name="ping", value=3)

        ping.save()

    return ping.value


def get_request_parameters():

    data = {}

    for name, value in zip(
            ['timeOut', 'reconnectTime', 'delayRequest'],
            [30000, 1000, 1000]
    ):

        param = IntParameter.objects.filter(name=name).first()

        if not param:

            param = IntParameter(name=name, value=value)

            param.save()

        data[name] = param.value

    return data
