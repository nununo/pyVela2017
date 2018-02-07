# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/network/protocol.py
# ----------------------------------------------------------------------------

from twisted.internet import protocol
from twisted.protocols import basic
from twisted import logger


_log = logger.Logger(namespace='inputs.network')



class ControlProtocol(basic.LineReceiver):

    def connectionMade(self):

        _log.info('connection made!')


    def lineReceived(self, line):

        _log.info('received {l!r}', l=line)
        try:
            level = int(line.strip())
        except Exception:
            _log.warn('ignored {l!r}', l=line)
        else:
            self.factory.input_manager.level(level, 'network')


    def rawDataReceived(self, data):

        _log.warn('unexpected data: {d!r}', d=data)


    def connectionLost(self, reason=protocol.connectionDone):

        _log.info('connection lost')



class ControlFactory(protocol.Factory):

    protocol = ControlProtocol

    def __init__(self, input_manager):

        self.input_manager = input_manager


# ----------------------------------------------------------------------------
# inputs/network/protocol.py
# ----------------------------------------------------------------------------
