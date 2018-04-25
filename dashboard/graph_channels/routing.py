from channels.routing import route
from dashboard.graph_channels.consumers import ws_connect, ws_disconnect
from dashboard.graph_channels.tasks import update_graph


channel_routing = [
    route('websocket.connect', ws_connect),
    route('websocket.disconnect', ws_disconnect),
    route("update-graph", update_graph),
]