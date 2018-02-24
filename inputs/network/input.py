# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/network/input.py
# ----------------------------------------------------------------------------

"""
The TCP network connection input.
"""


from twisted.internet import defer
from twisted import logger

from inputs import input_base
from . import protocol



_log = logger.Logger(namespace='inputs.network')



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
        _log.info('started: listening on {i}:{p}', i=self._interface, p=self._port)
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def stop(self):

        yield self._listening_port.stopListening()
        _log.info('stopped: no longer listening')


# ----------------------------------------------------------------------------
# inputs/network/input.py
# ----------------------------------------------------------------------------
