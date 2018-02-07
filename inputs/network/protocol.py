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

        _log.info('received {d!r}', d=line)
        try:
            level = int(line.strip())
        except:
            pass
        else:
            self.factory.input_manager.level(level, "network")

    def connectionLost(self, reason):

        _log.info('connection lost')


class ControlFactory(protocol.Factory):

    protocol = ControlProtocol

    def __init__(self, input_manager):

        self.input_manager = input_manager


# ----------------------------------------------------------------------------
# inputs/network/protocol.py
# ----------------------------------------------------------------------------
