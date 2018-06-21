from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter

import game.consumers
import game.routing
import dashboard.routing
import dashboard.consumers


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
                game.routing.websocket_urlpatterns
                + dashboard.routing.websocket_urlpatterns
        )
    ),

    'channel': ChannelNameRouter({
        'connection-consumer': dashboard.consumers.ConnectionConsumer
    }),

})