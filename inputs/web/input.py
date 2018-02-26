# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/web/input.py
# ----------------------------------------------------------------------------

"""
The web input.
"""


import os

from twisted.internet import defer
from twisted.web import server, static
from twisted import logger
from autobahn.twisted import resource

from inputs import input_base
from . import server as input_server



_log = logger.Logger(namespace='inputs.web')



class WebInput(input_base.InputBase):

    """
    The web input class.

    Serves a simple HTML + Javascript interface accepting websocket based
    control and pushing out useful monitoring information (so not strictly
    an input).
    """

    def __init__(self, reactor, wiring, interface='0.0.0.0', port=8080):

        super(WebInput, self).__init__(reactor, wiring)
        self._interface = interface
        self._port = port

        self._listening_port = None


    @defer.inlineCallbacks
    def start(self):

        ws_factory = input_server.WSFactory(self._wiring)
        ws_resource = resource.WebSocketResource(ws_factory)

        web_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'web-root'))
        root_resource = static.File(web_root, ignoredExts=('.gz',))
        root_resource.putChild(b'ws', ws_resource)
        site = server.Site(root_resource)

        self._listening_port = self._reactor.listenTCP(
            self._port,
            site,
            interface=self._interface,
        )
        _log.info('started: listening on {i}:{p}', i=self._interface, p=self._port)
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def stop(self):

        yield self._listening_port.stopListening()
        _log.info('stopped: no longer listening')


# ----------------------------------------------------------------------------
# inputs/web/input.py
# ----------------------------------------------------------------------------
