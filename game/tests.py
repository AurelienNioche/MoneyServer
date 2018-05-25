from game.models import User, Choice, TutorialChoice, Room, Receipt, ConsumerState
import game.room.dashboard


def reset_all():

    for table in (User, Choice, TutorialChoice, Room, Receipt, ConsumerState):
        table.objects.all().delete()


def check_choices():

    rm = Room.objects.first()

    for t in range(20):
        choices = Choice.objects.filter(room_id=rm.id, t=t, success=None)
        print(choices)

    markets = (0, 1), (1, 2), (2, 0)

    # print(choices.filter(desired_good=0, good_in_hand=0))

    for g1, g2 in markets:

        pools = [
            choices.filter(desired_good=g1, good_in_hand=g2),
            choices.filter(desired_good=g2, good_in_hand=g1)
        ]

        import numpy as np

        # We sort pools in order to get the shortest pool first
        idx_min, idx_max = np.argsort([p.count() for p in pools])
        min_pool, max_pool = pools[idx_min], pools[idx_max]

        # Shuffle the max pool
        max_pool = max_pool.order_by('?')

        # The firsts succeed
        for c1, c2 in zip(min_pool, max_pool):

            c1.success = True
            c2.success = True
            c1.save(update_fields=["success"])
            c2.save(update_fields=["success"])

        idx = min_pool.count()

        # The lasts fail
        for c in max_pool[idx:]:

            c.success = False
            c.save(update_fields=["success"])

        for c in zip(min_pool, max_pool):
            print(c.success)


reset_all()
