from django.db import transaction

from game.models import ConsumerTask


def task_is_done(demand, room_id, t=None):

    if demand == 'training_choice':
        return False

    with transaction.atomic():

        try:
            task = ConsumerTask.objects.select_for_update(nowait=True).filter(room_id=room_id, demand=demand, t=t).first()

            if not task:
                raise Exception(f'ConsumerTask missing entry: demand={demand}, room_id={room_id}, t={t}')

            return task.done

        except Exception as e:

            print(str(e))


def finished_treating_demand(task):
    task.done = True
    task.save(update_fields=['done'])


def treat_demand(demand, room_id, t=None):

    try:
        task = ConsumerTask.objects.select_for_update(nowait=True).filter(room_id=room_id, demand=demand, t=t).first()

        return task

    except Exception as e:
        print(str(e))






