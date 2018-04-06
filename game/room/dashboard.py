import numpy as np
from django.utils import timezone
from adminbase import settings

import os
import subprocess
import pickle

from game.models import Room
from parameters import parameters

from . import state


def delete(room_id):

    rm = Room.objects.filter(id=room_id).first()

    if rm:
        rm.delete()


def create(data):

    Room.objects.select_for_update().all()

    trial = bool(data['trial'])
    ending_t = int(data["ending_t"])


def get_list():

    rooms = Room.objects.all().order_by("id")
    users = User.objects.filter(registered=True)

    rooms_list = []

    for rm in rooms:

        users_room = [i for i in users.filter(room_id=rm.id)]

        dic = {"att": rm, "connected_players": users_room}
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
    db_name = "duopoly.sqlite3"
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

    for table in (Room, RoomComposition, Round, RoundComposition, Round, FirmPrice, FirmPosition, FirmProfit,
                  ConsumerChoice):

        entries = table.objects.all()
        entries.delete()


def get_rooms():

    room_info = dict()

    room_info["room_25_opp_score"] = "{} / {}".format(
        Room.objects.filter(display_opponent_score=True, opened=True, missing_players=2, radius=0.25).count(),
        Room.objects.filter(display_opponent_score=True, state="end", radius=0.25).count()
    )
    room_info["room_25_no_opp_score"] = "{} / {}".format(
        Room.objects.filter(display_opponent_score=True, opened=True, missing_players=2, radius=0.25).count(),
        Room.objects.filter(display_opponent_score=True, state="end", radius=0.25).count()
    )
    room_info["room_50_opp_score"] = "{} / {}".format(
        Room.objects.filter(display_opponent_score=True, opened=True, missing_players=2, radius=0.50).count(),
        Room.objects.filter(display_opponent_score=True, state="end", radius=0.50).count()
    )
    room_info["room_50_no_opp_score"] = "{} / {}".format(
        Room.objects.filter(display_opponent_score=True, opened=True, missing_players=2, radius=0.50).count(),
        Room.objects.filter(display_opponent_score=True, state="end", radius=0.50).count()
    )

    return room_info
