# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# webserver/server.py
# ----------------------------------------------------------------------------

"""
An asyncronous, Twisted/Autobahn based, HTTP/websocket server.
"""

from datetime import datetime
import json
import os

from zope.interface import provider
from twisted import logger
from twisted.web import server, static

from autobahn.twisted import websocket
from autobahn.twisted import resource

import log



_log = logger.Logger(namespace='inputs.web')



@provider(logger.ILogObserver)
class WSProto(websocket.WebSocketServerProtocol):

    """
    Server side websocket implementation.

    Works along with its factory which tracks the most recent, if any, websocket
    connection which will be considered the only one that is active and towards
    which server pushed messages will be sent.
    """

    def onConnect(self, request):

        # Twisted/Autobahn calls this when a websocket connection is establised.

        # Add self as a log observer to push logs to the client.
        log.add_observer(self)

        # Handle `arduino_raw_data` by pushing it to the client.
        self.factory.event_manager.arduino_raw_data.calls(self._push_raw_data)


    def onOpen(self):

        # Twisted/Autobahn calls this when a websocket connection is ready.

        _log.warn('{p.host}:{p.port} connected', p=self.transport.getPeer())


    def onMessage(self, payload, isBinary):

        # Twisted/Autobahn calls this when a websocket message is received.

        _log.debug('ws mesg: p={p!r} b={b!r}', p=payload, b=isBinary)

        try:
            message = json.loads(payload.decode('utf-8'))
        except ValueError:
            _log.warn('invalid payload ignored: {p!r}', p=payload)
        else:
            method_name = '_action_%s' % message.get('action', 'invalid')
            method = getattr(self, method_name, self._action_invalid)
            method(message)


    @staticmethod
    def _action_invalid(message):

        _log.warn('invalid message: {m!r}', m=message)


    def _action_change_level(self, message):

        try:
            level = message['level']
        except KeyError:
            _log.warn('missing level: {m!r}', m=message)
        else:
            self.factory.event_manager.change_play_level(level, comment='web')


    def _action_set_log_level(self, message):

        try:
            namespace = message['namespace']
            level = message['level']
        except KeyError:
            _log.warn('missing level/namespace: {m!r}', m=message)
        else:
            self.factory.event_manager.set_log_level(namespace, level)
            # Log message on the specified logger/level to feed user back.
            level = logger.LogLevel.levelWithName(level)
            logger.Logger(namespace=namespace).emit(level, 'log level set')


    def onClose(self, wasClean, code, reason):

        # Twisted/Autobahn calls this when a websocket connection is closed.

        # Can't push logs to the client anymore.
        log.remove_observer(self)

        # Can't push arduino raw data to the client anymore.
        self.factory.event_manager.arduino_raw_data.no_longer_calls(self._push_raw_data)

        _log.warn('{p.host}:{p.port} disconnected', p=self.transport.getPeer())


    def _send_message_dict(self, message_type, message_dict):

        # Server to client messages are JSON serialized objects.

        message_dict['type'] = message_type
        msg = json.dumps(message_dict).encode('utf8')
        self.sendMessage(msg, isBinary=False)


    def _push_raw_data(self, **values):

        """
        Called by our factory to send raw data to the client.

        Raw data is an object containing time and an integer reading which
        the client will plot in a chart.
        """

        values['ts'] = datetime.now().isoformat()
        self._send_message_dict('chart-data', values)


    def __call__(self, event):

        # Called by Twisted when delivering a log event to this observer.

        # Format a message with four space-separated elements:
        # - Fixed width, capitalized first letter of log level.
        # - Fixed width, seconds and milliseconds of event timestamp.
        # - Variable width, logger namespace.
        # - Variable width, formatted message itself.

        log_datetime = datetime.fromtimestamp(event['log_time'])
        log_message = '%s %s %s %s' % (
            event['log_level'].name[0].upper(),
            log_datetime.strftime('%S.%f')[:6],
            event.get('log_namespace', '-'),
            logger.formatEvent(event),
        )

        self._send_message_dict('log-message', {
            'message': log_message,
        })



class WSFactory(websocket.WebSocketServerFactory):

    """
    Twisted protocol factory for the server side websocket protocol.
    """

    protocol = WSProto

    def __init__(self, event_manager, *args, **kwargs):

        # Protocol instances use `event_manager`.

        super(WSFactory, self).__init__(*args, **kwargs)
        self.event_manager = event_manager



def start(reactor, event_manager, interface, port):

    """
    Starts listening for HTTP connections.
    """

    ws_factory = WSFactory(event_manager)
    ws_resource = resource.WebSocketResource(ws_factory)

    web_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'web-root'))
    root_resource = static.File(web_root, ignoredExts=('.gz',))
    root_resource.putChild(b'ws', ws_resource)
    site = server.Site(root_resource)

    reactor.listenTCP(port, site, interface=interface)
    _log.warn('listening for HTTP on {i}:{p}', i=interface, p=port)


# ----------------------------------------------------------------------------
# webserver/server.py
# ----------------------------------------------------------------------------
