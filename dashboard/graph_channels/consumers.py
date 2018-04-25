from channels.auth import channel_session_user
from channels import Group
from channels import Channel
import json


@channel_session_user
def ws_connect(message):

    room_id = message.content.get("path").split("/")[-1]

    message.channel_session["room-group"] = room_id

    Group('test').add(message.reply_channel)

    r = {
        "message": "Connection accepted!"
    }

    message.reply_channel.send({
        'accept': True,
        'text': json.dumps(r)
    })

    Channel("update-graph").send({"room_id": room_id})


@channel_session_user
def ws_disconnect(message):

    room_id = message.channel_session["room-group"]
    Group(f'update-graph-room-{room_id}').discard(message.reply_channel)
