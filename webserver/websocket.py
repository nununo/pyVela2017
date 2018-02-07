#!/usr/bin/env python

import datetime
import json

from twisted import logger

from autobahn.twisted import websocket



_log = logger.Logger(namespace='webserver.ws')



class WSProto(websocket.WebSocketServerProtocol):

    def _log_state(self, msg=''):
        _log.info('{m}', m=msg)

    def onConnect(self, request):
        self._log_state('ws conn')
        self.factory.connected_protocol = self

    def onOpen(self):
        self._log_state('ws open')

    def onMessage(self, payload, binary):
        msg = 'ws mesg: p={p!r} b={b!r}'.format(p=payload, b=binary)
        self._log_state(msg)

    def onClose(self, wasClean, code, reason):
        self._log_state('ws clse')
        self.factory.connected_protocol = None

    def _send(self, message_dict):
        msg = json.dumps(message_dict).encode('utf8')
        self.sendMessage(msg, False)

    def raw(self, source, value):
        self._send({
            't': datetime.datetime.now().isoformat(),
            'y': value,
        })

    def log_message(self, text):
        self._send({
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
