from django.db import transaction

from game.models import BoolParameter


def is_trial():

    with transaction.atomic():

        trial = BoolParameter.objects.filter(name="trial").first()
        skip_survey = BoolParameter.objects.filter(name="skip_survey").first()
        skip_tutorial = BoolParameter.objects.filter(name="skip_tutorial").first()

        if not trial:

            trial = BoolParameter(name="trial", value=False)
            trial.save()

        if not skip_survey:

            skip_survey = BoolParameter(name="skip_survey", value=True)
            skip_survey.save()

        if not skip_tutorial:

            skip_tutorial = BoolParameter(name="skip_tutorial", value=True)
            skip_tutorial.save()

        return trial.value, skip_survey.value, skip_tutorial.value


def create_default_room():

    with transaction.atomic():

        auto_room = BoolParameter.objects.filter(name="auto_room").first()

        if not auto_room:

            auto_room = BoolParameter(name="auto_room", value=True)
            auto_room.save()

        return auto_room.value
