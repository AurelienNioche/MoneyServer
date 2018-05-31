from django.db import transaction

from game.models import ConsumerState


def is_consumer_already_treating_demand(demand, room_id, t=None):

    with transaction.atomic():
        s = ConsumerState.objects.select_for_update().filter(room_id=room_id).first()

        if not s:

            s = ConsumerState(room_id=room_id)
            s.save()

        # If demand is training_choice
        # We want do not the consumer to wait between each treatment
        # because each verification are individual
        # so it will take much longer time
        # to process if we do that
        if demand == 'training_choice':
            return False

        # If demand is choice we also want to check for
        # the t (the worker may treat multiple t simultaneously)
        if demand == 'choice':
            return getattr(s, demand) and str(t) in s.treating_t.split('/')

        return getattr(s, demand)


def get(room_id):

    with transaction.atomic():
        return ConsumerState.objects.select_for_update().filter(room_id=room_id).first()


def finished_treating_demand(demand, room_id, t=None):

    with transaction.atomic():

        s = ConsumerState.objects.select_for_update().filter(room_id=room_id).first()
        setattr(s, demand, False)

        if t:
            # Remove t
            t_list = s.treating_t.split('/')
            t_list.remove(str(t))
            # Rebuild the string
            s.treating_t = '/'.join(t_list)

        s.save()


def treat_demand(demand, room_id, t=None):

    with transaction.atomic():

        s = ConsumerState.objects.select_for_update().filter(room_id=room_id).first()
        setattr(s, demand, True)

        if t:
            s.treating_t += f'/{t}'

        s.save()




