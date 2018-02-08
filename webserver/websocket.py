# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# webserver/websocket.py
# ----------------------------------------------------------------------------

import datetime
import json

from twisted import logger

from autobahn.twisted import websocket



_log = logger.Logger(namespace='webserver.ws')



class WSProto(websocket.WebSocketServerProtocol):

    def onConnect(self, request):
        _log.info('ws conn')
        self.factory.connected_protocol = self

    def onOpen(self):
        _log.info('ws open')

    def onMessage(self, payload, isBinary):
        _log.info('ws mesg: p={p!r} b={b!r}', p=payload, b=isBinary)

    def onClose(self, wasClean, code, reason):
        _log.info('ws clse')
        self.factory.connected_protocol = None

    def _send_message_dict(self, message_dict):
        msg = json.dumps(message_dict).encode('utf8')
        self.sendMessage(msg, False)

    def raw(self, _source, value):
        self._send_message_dict({
            't': datetime.datetime.now().isoformat(),
            'y': value,
        })

    def log_message(self, text):
        self._send_message_dict({
            'text': text,
        })



class WSFactory(websocket.WebSocketServerFactory):

    protocol = WSProto

    def __init__(self, *args, **kwargs):
        super(WSFactory, self).__init__(*args, **kwargs)
        self.connected_protocol = None

    def raw(self, source, value):
        if self.connected_protocol:
            self.connected_protocol.raw(source, value)

    def log_message(self, message):
        if self.connected_protocol:
            self.connected_protocol.log_message(message)


def setup_websocket(reactor):

    factory = WSFactory()

    reactor.listenTCP(8081, factory, interface='0.0.0.0')
    _log.info('listening for WSCK connections on 0.0.0.0:8081')

    return factory


# ----------------------------------------------------------------------------
# webserver/websocket.py
# ----------------------------------------------------------------------------
