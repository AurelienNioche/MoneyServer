from django.db import transaction

from game.models import ConsumerState


def is_consumer_already_treating_demand(demand, room_id):

    with transaction.atomic():
        s = ConsumerState.objects.select_for_update().filter(room_id=room_id).first()

        if not s:

            s = ConsumerState(room_id=room_id)
            s.save()

        print('wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww')
        print(getattr(s, demand))
        return getattr(s, demand)


def get(room_id):

    with transaction.atomic():
        return ConsumerState.objects.select_for_update().filter(room_id=room_id).first()


def finished_treating_demand(demand, room_id):

    with transaction.atomic():

        s = ConsumerState.objects.select_for_update().filter(room_id=room_id).first()
        setattr(s, demand, False)

        s.save()


def treat_demand(demand, room_id):

    with transaction.atomic():

        s = ConsumerState.objects.select_for_update().filter(room_id=room_id).first()
        setattr(s, demand, True)

        s.save()




