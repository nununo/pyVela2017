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

from .common import log



class ControlProtocol(basic.LineReceiver):

    """
    Line based control protocol.

    Lines should be terminated by CRLF.
    Accepts single digit lines that notify the input manager of such level
    change requests.
    """

    def connectionMade(self):

        # Called by Twisted for each established connection.

        log.info('connection made!')


    def lineReceived(self, line):

        # Called by Twisted for each CRLF terminated line received.

        log.info('received {l!r}', l=line)
        try:
            level = int(line.strip())
        except Exception:
            log.warn('ignored {l!r}', l=line)
        else:
            self.factory.event_manager.change_play_level(level, 'network')


    def rawDataReceived(self, data):

        # Called by Twisted if the protocol goes to "raw" mode.
        # Should not happen, given that this code never triggers it.
        # It is here to ensure a complete protocol implementation, given that
        # the parent class does not implement it.

        log.warn('unexpected data: {d!r}', d=data)


    def connectionLost(self, reason=protocol.connectionDone):

        # Called by Twisted after a connection is terminated.

        log.info('connection lost')



class ControlFactory(protocol.Factory):

    """
    Line based control protocol factory.
    """

    protocol = ControlProtocol

    def __init__(self, event_manager):

        # The event manager is used to fire `change_play_level` events.

        self.event_manager = event_manager

        # Twisted not to log messages about us.
        self.noisy = False


# ----------------------------------------------------------------------------
# inputs/network/protocol.py
# ----------------------------------------------------------------------------
