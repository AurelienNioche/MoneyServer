from game.models import User, Room, Choice

import game.user.client


def submit_choice(desired_good, user_id, t):

    u = User.objects.get(id=user_id)
    rm = Room.objects.get(id=u.room_id)

    last_choice = Choice.objects.filter(t=t-1, user_id=user_id).first()

    if last_choice and last_choice.good_in_hand != u.consumption_good:
        good_in_hand = last_choice.good_in_hand
    else:
        good_in_hand = u.production_good

    current_choice = Choice.objects.filter(room_id=rm.id, t=t, desired_good=None).first()

    if current_choice:

        current_choice.user_id = user_id
        current_choice.desired_good = game.user.client.get_absolute_good(u, desired_good)
        current_choice.good_in_hand = good_in_hand

        current_choice.save()

    # If choice entries are filled for this t, match players' choice
    else:

        _matching(rm, t)


def _matching(rm, t):

    choices = Choice.objects.filter(room_id=rm.id, t=t)





