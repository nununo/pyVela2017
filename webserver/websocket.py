#!/usr/bin/env python

from twisted import logger

from autobahn.twisted import websocket



_log = logger.Logger(namespace='webserver.ws')



class WSProto(websocket.WebSocketServerProtocol):

    def __init__(self):
        super(WSProto, self).__init__()

    def _log_state(self, msg=''):
        _log.info('{m}', m=msg)

    def onConnect(self, request):
        self._log_state('ws conn')

    def onOpen(self):
        self._log_state('ws open')

    def onMessage(self, payload, binary):
        msg = 'ws mesg: p={p!r} b={b!r}'.format(p=payload, b=binary)
        self._log_state(msg)

    def onClose(self, wasClean, code, reason):
        self._log_state('ws clse')



def setup_websocket(reactor):

    factory = websocket.WebSocketServerFactory()
    factory.protocol = WSProto

    reactor.listenTCP(8081, factory, interface='0.0.0.0')
    _log.info('listening for WSCK connections on 0.0.0.0:8081')
