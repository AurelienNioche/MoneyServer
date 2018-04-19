from game.models import BoolParameter
import game.params.client


def get_parameters():

    params = BoolParameter.objects.all().order_by('name')

    if params.count() != 4:

        game.params.client.is_trial()
        game.params.client.create_default_room()

        params = BoolParameter.objects.all().order_by('name')

    for p in params:
        p.proper_name = p.name.capitalize().replace('_', ' ')

    return params


def set_parameter(name, value):

    p = BoolParameter.objects.filter(name=name).first()

    if p:
        p.value = value
        p.save(update_fields=['value'])
