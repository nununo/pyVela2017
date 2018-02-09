# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/network/protocol.py
# ----------------------------------------------------------------------------

"""
Twisted implementation of the network input protocol.
"""

from twisted.internet import protocol
from twisted.protocols import basic
from twisted import logger


_log = logger.Logger(namespace='inputs.network')



class ControlProtocol(basic.LineReceiver):

    """
    Line based control protocol.

    Lines should be terminated by CRLF.
    Accepts single digit lines that notify the input manager of such level
    change requests.
    """

    def connectionMade(self):

        # Called by Twisted for each established connection.

        _log.info('connection made!')


    def lineReceived(self, line):

        # Called by Twisted for each CRLF terminated line received.

        _log.info('received {l!r}', l=line)
        try:
            level = int(line.strip())
        except Exception:
            _log.warn('ignored {l!r}', l=line)
        else:
            self.factory.input_manager.level(level, 'network')


    def rawDataReceived(self, data):

        # Called by Twisted if the protocol goes to "raw" mode.
        # Should not happen, given that this code never triggers it.
        # It is here to ensure a complete protocol implementation, given that
        # the parent class does not implement it.

        _log.warn('unexpected data: {d!r}', d=data)


    def connectionLost(self, reason=protocol.connectionDone):

        # Called by Twisted after a connection is terminated.

        _log.info('connection lost')



class ControlFactory(protocol.Factory):

    """
    Line based control protocol factory.
    """

    protocol = ControlProtocol

    def __init__(self, input_manager):

        # Need to keep track of the input manager such that protocol instances
        # can notify it about level change requests.

        self.input_manager = input_manager


# ----------------------------------------------------------------------------
# inputs/network/protocol.py
# ----------------------------------------------------------------------------
