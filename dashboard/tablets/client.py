from django.utils import timezone
import datetime
from dashboard.models import ConnectedTablet, IntParameter
from game.models import User

import dashboard.views


def get_connection_table():

    devices = get_connected_users()
    return get_table_from_devices(devices)


def get_table_from_devices(devices):
    return dashboard.views.ConnectedTablets.get_table_from_devices(devices)


def get_connected_users():

    devices = ConnectedTablet.objects.all().order_by('tablet_id')

    for d in devices:
        connected = not _is_disconnected(d.time_last_request)
        if connected != d.connected:
            d.connected = connected
            d.save(update_fields=["connected"])

    return devices


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

