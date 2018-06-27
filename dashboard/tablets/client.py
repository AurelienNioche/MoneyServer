from django.utils import timezone
import datetime
from dashboard.models import ConnectedTablet, IntParameter
from game.models import User, Room, Choice, TutorialChoice

import dashboard.views


def get_connection_table():

    info = get_overview_info()

    return get_html_table(info)


def get_html_table(info):
    return dashboard.views.ConnectedTablets.get_html_table(info)


def get_overview_info():

    devices = ConnectedTablet.objects.all().order_by('tablet_id')

    update_devices(devices)

    active_room = Room.objects.filter(opened=True).first()

    if not active_room:
        error = 'No room opened!'

        return {'error': error}

    else:
        error = None

    state = active_room.state

    t = active_room.t if state == 'game' else None

    users = get_connected_users(devices, active_room)

    users_replied = who_replied(state, users, t)

    return {'t': t, 'state': state, 'users': users_replied, 'error': error}


def who_replied(state, users, t):

    """
    Gets reply boolean (replied or not) for each user depending on the state
    """

    if state == 'survey':

        for u in users:

            u.replied = u.age != -1

        return users

    elif state == 'training':

        for u in users:

            choices = TutorialChoice.objects.filter(player_id=u.player_id, room_id=u.room_id)\
                    .exclude(desired_good=None)\
                    .values_list('t')

            if choices:
                u.training_t = max(choices)[0]
            else:
                u.training_t = 0

            u.replied = u.training_done

        return users

    elif state == 'game':

        for u in users:

            choice = Choice.objects.filter(t=t, player_id=u.player_id, room_id=u.room_id).first()
            u.replied = choice.desired_good is not None

        return users

    else:

        for u in users:
            u.replied = True

        return users


def get_connected_users(devices, active_room):

    users = User.objects.filter(
        room_id=active_room.id, tablet_id__in=[d.tablet_id for d in devices]
    ).order_by('tablet_id')

    for u in users:

        d = devices.get(tablet_id=u.tablet_id)

        if d:

            connected = not _is_disconnected(d.time_last_request)

            u.connected = connected

            if connected != d.connected:
                d.connected = connected
                d.save(update_fields=["connected"])
        else:
            raise Exception('No device associated')

    return users


def update_devices(devices):

    for d in devices:

        connected = not _is_disconnected(d.time_last_request)

        if connected != d.connected:
            d.connected = connected
            d.save(update_fields=["connected"])


def _is_disconnected(reference_time):

    # Then get the timezone
    tz_info = reference_time.tzinfo
    # Get time now using timezone info
    t_now = datetime.datetime.now(tz_info)

    param = IntParameter.objects.filter(name="disconnected_timeout").first()

    if param is None:

        param = IntParameter(name="disconnected_timeout", value=15)
        param.save()

    delta = datetime.timedelta(seconds=param.value)

    # If more than X seconds since the last request
    timeout = t_now > reference_time + delta

    return timeout


def register_tablet(device_id, tablet_id):

    t = ConnectedTablet.objects.filter(device_id=device_id).first()

    if t:

        t.delete()

    t = ConnectedTablet(
        device_id=device_id,
        tablet_id=tablet_id,
        connected=False,
        time_last_request=timezone.now()
    )

    t.save()


def set_time_last_request(user_id, device_id):

    if device_id:

        device = ConnectedTablet.objects.get(device_id=device_id)

    elif user_id:

        device = ConnectedTablet.objects.get(
            device_id=User.objects.get(id=user_id).device_id
        )

    else:
        raise Exception('Arguments user_id or device_id are needed.')

    device.time_last_request = timezone.now()

    device.save(update_fields=['time_last_request'])

