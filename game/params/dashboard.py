from game.models import BoolParameter


def get_parameters():
    params = BoolParameter.objects.all().order_by('name')

    for p in params:
        p.proper_name = p.name.capitalize().replace('_', ' ')

    return params


def set_parameter(name, value):

    p = BoolParameter.objects.filter(name=name).first()

    if p:
        p.value = value
        p.save(update_fields=['value'])
