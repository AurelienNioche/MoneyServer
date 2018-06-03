from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter

import game.consumers
import game.routing


application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            game.routing.websocket_urlpatterns
        )
    ),

    'channel': ChannelNameRouter({
        'receipt-consumer': game.consumers.ReceiptConsumer,
        'ping-consumer': game.consumers.PingConsumer,
    }),

})