# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/web/server.py
# ----------------------------------------------------------------------------

"""
An asyncronous, Twisted/Autobahn based, HTTP/websocket server.
"""

from datetime import datetime
import json

from zope.interface import provider
from twisted import logger

from autobahn.twisted import websocket

import log as log_package



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
        log_package.add_observer(self)

        # Handle `agd_output` by pushing it as chart data to the client.
        self.factory.wiring.wire.agd_output.calls_to(self._push_chart_data)


    def onOpen(self):

        # Twisted/Autobahn calls this when a websocket connection is ready.

        _log.warn('{p.host}:{p.port} connected', p=self.transport.getPeer())

        # Push known thresholds if available
        for level, value in self.factory.agd_thresholds.items():
            self._push_agd_threshold(level, value)

        self.factory.wiring.wire.notify_agd_threshold.calls_to(
            self._push_agd_threshold
        )


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
            self.factory.wiring.change_play_level(level, comment='web')


    def _action_set_threshold(self, message):

        try:
            level = message['level']
            value = message['value']
        except KeyError:
            _log.warn('missing level/value: {m!r}', m=message)
        else:
            self.factory.wiring.set_agd_threshold(level, value)


    def _action_set_log_level(self, message):

        try:
            namespace = message['namespace']
            level = message['level']
        except KeyError:
            _log.warn('missing level/namespace: {m!r}', m=message)
        else:
            self.factory.wiring.set_log_level(namespace, level)
            # Log message on the specified logger/level to feed user back.
            level = logger.LogLevel.levelWithName(level)
            logger.Logger(namespace=namespace).emit(level, 'log level set')


    def onClose(self, wasClean, code, reason):

        # Twisted/Autobahn calls this when a websocket connection is closed.

        # Can't push logs to the client anymore.
        log_package.remove_observer(self)

        # Can't push chart data to the client anymore.
        self.factory.wiring.unwire.agd_output.calls_to(self._push_chart_data)

        # Can't push threshold updates to the client anymore.
        self.factory.wiring.wire.notify_agd_threshold.calls_to(
            self._push_agd_threshold
        )

        _log.warn('{p.host}:{p.port} disconnected', p=self.transport.getPeer())


    def _send_message_dict(self, message_type, message_dict):

        # Server to client messages are JSON serialized objects.

        message_dict['type'] = message_type
        msg = json.dumps(message_dict).encode('utf8')
        self.sendMessage(msg, isBinary=False)


    def _push_chart_data(self, **values):

        """
        Pushes `values` as chart data updates to the client, adding a `ts`
        property with the current timestamp.
        """

        values['ts'] = datetime.now().isoformat()
        self._send_message_dict('chart-data', values)


    def _push_agd_threshold(self, level, value):

        """
        """

        self._send_message_dict('chart-threshold', {
            "level": level,
            "value": value,
        })
        _log.info("sent agd threshold: {l!r}={v!r}", v=value, l=level)


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

    def __init__(self, wiring, *args, **kwargs):

        super(WSFactory, self).__init__(*args, **kwargs)

        self.agd_thresholds = {}

        # Used by protocol to call `change_play_level` and `set_log_level`.
        self.wiring = wiring

        wiring.wire.notify_agd_threshold.calls_to(self._store_agd_threshold)


    def _store_agd_threshold(self, level, value):

        self.agd_thresholds[level] = value


# ----------------------------------------------------------------------------
# inputs/web/server.py
# ----------------------------------------------------------------------------
