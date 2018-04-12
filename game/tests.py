from game.models import User, Choice, TutorialChoice, Room


def reset_all():

    for table in (User, Choice, TutorialChoice, Room):
        table.objects.all().delete()


reset_all()