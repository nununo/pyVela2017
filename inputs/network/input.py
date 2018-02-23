# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/network/input.py
# ----------------------------------------------------------------------------

"""
The TCP network connection input.
"""


from twisted.internet import defer

from inputs import input_base
from . import protocol


class NetworkInput(input_base.InputBase):

    def __init__(self, reactor, event_manager, interface='0.0.0.0', port=10000):

        super(NetworkInput, self).__init__(reactor, event_manager)
        self._interface = interface
        self._port = port

        self._factory = protocol.ControlFactory(event_manager)
        self._listening_port = None


    @defer.inlineCallbacks
    def start(self):

        self._listening_port = self._reactor.listenTCP(
            self._port,
            self._factory,
            interface=self._interface
        )
        yield defer.succeed(None)


# ----------------------------------------------------------------------------
# inputs/network/input.py
# ----------------------------------------------------------------------------
