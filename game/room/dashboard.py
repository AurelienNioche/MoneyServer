from django.utils import timezone
from adminbase import settings

import os
import subprocess
import pickle

from game.models import Room, Choice, TutorialChoice
import game.room.state


def delete(room_id):

    rm = Room.objects.filter(id=room_id).first()

    if rm:

        Choice.objects.filter(room_id=rm.id).delete()
        TutorialChoice.objects.filter(room_id=rm.id).delete()
        rm.delete()


def create(data):

    t_max = int(data["t_max"])
    tutorial_t_max = int(data["tutorial_t_max"])

    count_type = [int(v) for k, v in data.items() if k.startswith("x")]
    n_user = sum(count_type)
    n_type = len(count_type)

    types = [i for i in range(n_type) for _ in range(count_type[i])]

    rm = Room(
        t_max=t_max,
        tutorial_t_max=tutorial_t_max,
        t=0,
        tutorial_t=0,
        state=game.room.state.states.welcome,
        opened=True,
        n_user=n_user,
        n_type=n_type,
        types="/".join([str(i) for i in count_type])
    )

    rm.save()

    types = [i for i in range(n_type) for _ in range(count_type[i])]

    Choice.objects.bulk_create([
        Choice(
            room_id=rm.id,
            t=t,
            player_id=n,
            user_id=None,
            good_in_hand=types[n] if not t else None,
            desired_good=None,
            success=None,
        )
        for n in range(n_user) for t in range(t_max)
    ])

    TutorialChoice.objects.bulk_create([
        TutorialChoice(
            room_id=rm.id,
            t=t,
            player_id=n,
            user_id=None,
            good_in_hand=types[n] if not t else None,
            desired_good=None,
            success=None
        )
        for n in range(n_user) for t in range(tutorial_t_max)
    ])


def get_list():

    rooms = Room.objects.all().order_by("id")
    rooms_list = []

    for rm in rooms:
        dic = {"att": rm}
        rooms_list.append(dic)

    return rooms_list


def get_path(dtype):

    class Data:
        time_stamp = str(timezone.datetime.now()).replace(" ", "_")
        file_name = "{}_{}_.{}".format(dtype, time_stamp, dtype)
        folder_name = "game_data"
        folder_path = os.getcwd() + "/static/" + folder_name
        file_path = folder_path + "/" + file_name
        to_return = folder_name + "/" + file_name

    os.makedirs(Data.folder_path, exist_ok=True)

    return Data()


def convert_data_to_pickle():

    mydata = get_path("p")
    d = {}

    for table in (
            Room,
    ):
        # Convert all entries to valid pure python
        attr = list(vars(i) for i in table.objects.all())
        valid_attr = [{k: v for k, v in i.items() if type(v) in (bool, int, str, float)} for i in attr]

        d[table.__name__] = valid_attr

    pickle.dump(file=open(mydata.file_path, "wb"), obj=d)

    return mydata.to_return


def convert_data_to_sqlite():

    db_source = settings.DATABASES["default"]["NAME"]

    sql_file = get_path("sql")
    db_name = "money.sqlite3"
    db_path = sql_file.folder_path + "/" + db_name
    to_return = sql_file.folder_name + "/" + db_name

    subprocess.call("pg_dump -U dasein {} > {}".format(db_source, sql_file.file_path), shell=True)

    subprocess.call("rm {}".format(db_path), shell=True)
    subprocess.call("java -jar pg2sqlite.jar -d {} -o {}".format(sql_file.file_path, db_path), shell=True)

    return to_return


def flush_db():

    os.makedirs("dumps", exist_ok=True)

    subprocess.call("pg_dump -U dasein {} > dumps/dump_$(date +%F).sql".format(
        settings.DATABASES["default"]["NAME"]
    ), shell=True)

    for table in (None, ):

        entries = table.objects.all()
        entries.delete()
