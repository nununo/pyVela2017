# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# webserver/websocket.py
# ----------------------------------------------------------------------------

"""
An asyncronous, Twisted/Autobahn based, websocket server.
"""

import datetime
import json

from twisted import logger

from autobahn.twisted import websocket



_log = logger.Logger(namespace='webserver.ws')



class WSProto(websocket.WebSocketServerProtocol):

    """
    Server side websocket implementation.

    Works along with its factory which tracks the most recent, if any, websocket
    connection which will be considered the only one that is active and towards
    which server pushed messages will be sent.
    """

    def onConnect(self, request):

        # Twisted/Autobahn calls this when a websocket connection is establised.

        _log.info('ws conn')
        self.factory.connected_protocol = self


    def onOpen(self):

        # Twisted/Autobahn calls this when a websocket connection is ready.

        _log.info('ws open')


    def onMessage(self, payload, isBinary):

        # Twisted/Autobahn calls this when a websocket message is received.

        _log.info('ws mesg: p={p!r} b={b!r}', p=payload, b=isBinary)

        try:
            level = int(payload)
        except ValueError:
            _log.warn('invalid payload ignored')
        else:
            self.factory.change_level_callable(level)


    def onClose(self, wasClean, code, reason):

        # Twisted/Autobahn calls this when a websocket connection is closed.

        _log.info('ws clse')
        self.factory.connected_protocol = None


    def _send_message_dict(self, message_dict):

        # Server to client messages are JSON serialized objects.

        msg = json.dumps(message_dict).encode('utf8')
        self.sendMessage(msg, isBinary=False)


    def raw(self, _source, value):

        """
        Called by our factory to send raw data to the client.

        Raw data is an object containing time and an integer reading which
        the client will plot in a chart.
        """

        self._send_message_dict({
            't': datetime.datetime.now().isoformat(),
            'y': value,
        })


    def log_message(self, text):

        """
        Called by our factory to send log messages to the client.

        Log messages are objects with a single 'text' attribute and will be
        displayed by the client.
        """

        self._send_message_dict({
            'text': text,
        })



class WSFactory(websocket.WebSocketServerFactory):

    """
    Twisted protocol factory for the server side websocket protocol.
    """

    protocol = WSProto

    def __init__(self, change_level_callable, *args, **kwargs):

        # Track a single `connected_protocol` so that we can push data.

        super(WSFactory, self).__init__(*args, **kwargs)
        self.connected_protocol = None
        self.change_level_callable = change_level_callable


    def raw(self, source, value):

        """
        Sends a raw `value` from `source` to the connected protocol, if any.
        """

        if self.connected_protocol:
            self.connected_protocol.raw(source, value)


    def log_message(self, message):

        """
        Sends the log `message` to the connected protocol, if any.
        """

        if self.connected_protocol:
            self.connected_protocol.log_message(message)



def setup_websocket(reactor, change_level_callable):

    """
    Starts listening for websocket connections.
    """

    factory = WSFactory(change_level_callable)

    # TODO: Should port/interface be configurable? Client may need adjustments.
    reactor.listenTCP(8081, factory, interface='0.0.0.0')
    _log.info('listening for WSCK connections on 0.0.0.0:8081')

    return factory


# ----------------------------------------------------------------------------
# webserver/websocket.py
# ----------------------------------------------------------------------------
