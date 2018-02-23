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
from autobahn.twisted import resource

from inputs import input_base
from . import server as input_server



class WebInput(input_base.InputBase):

    def __init__(self, reactor, event_manager, interface='0.0.0.0', port=8080):

        super(WebInput, self).__init__(reactor, event_manager)
        self._interface = interface
        self._port = port

        self._listening_port = None


    @defer.inlineCallbacks
    def start(self):

        ws_factory = input_server.WSFactory(self._event_manager)
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
#        _log.warn('listening for HTTP on {i}:{p}', i=interface, p=port)
        yield defer.succeed(None)


# ----------------------------------------------------------------------------
# inputs/web/input.py
# ----------------------------------------------------------------------------
