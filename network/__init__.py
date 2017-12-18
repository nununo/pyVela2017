
from twisted.internet import protocol
from twisted.protocols import basic
from twisted import logger


_log = logger.Logger(namespace='sensor')


class ControlProtocol(basic.LineReceiver):

    def connectionMade(self):

        _log.info('connection made!')


    def dataReceived(self, data):

        _log.info('received {d!r}', d=data)
        try:
            level = int(data.strip())
            self.factory.player_mgr.level(level)
        except:
            pass

    def connectionLost(self, reason):

        _log.info('connection lost')


class ControlFactory(protocol.Factory):

    protocol = ControlProtocol

    def __init__(self, player_mgr):

        self.player_mgr = player_mgr


