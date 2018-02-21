# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# webserver/websocket.py
# ----------------------------------------------------------------------------

"""
An asyncronous, Twisted/Autobahn based, websocket server.
"""

import datetime
import json

from twisted import logger

from autobahn.twisted import websocket



_log = logger.Logger(namespace='webserver.ws')



class WSProto(websocket.WebSocketServerProtocol):

    """
    Server side websocket implementation.

    Works along with its factory which tracks the most recent, if any, websocket
    connection which will be considered the only one that is active and towards
    which server pushed messages will be sent.
    """

    def onConnect(self, request):

        # Twisted/Autobahn calls this when a websocket connection is establised.

        _log.info('ws conn')
        self.factory.set_active_protocol(self)


    def onOpen(self):

        # Twisted/Autobahn calls this when a websocket connection is ready.

        _log.info('ws open')


    def onMessage(self, payload, isBinary):

        # Twisted/Autobahn calls this when a websocket message is received.

        _log.info('ws mesg: p={p!r} b={b!r}', p=payload, b=isBinary)

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
            self.factory.event_manager.fire('change-level', level, comment='web')


    def _action_set_log_level(self, message):

        try:
            namespace = message['namespace']
            level = message['level']
        except KeyError:
            _log.warn('missing level/namespace: {m!r}', m=message)
        else:
            self.factory.event_manager.fire('set-log-level', namespace, level)
            # Log message on the specified logger/level to feed user back.
            log = logger.Logger(namespace=namespace)
            method = getattr(log, level)
            method('log level set')


    def onClose(self, wasClean, code, reason):

        # Twisted/Autobahn calls this when a websocket connection is closed.

        _log.info('ws clse')
        self.factory.set_protocol_gone(self)


    def _send_message_dict(self, message_type, message_dict):

        # Server to client messages are JSON serialized objects.

        message_dict['type'] = message_type
        msg = json.dumps(message_dict).encode('utf8')
        self.sendMessage(msg, isBinary=False)


    def push_raw_data(self, **values):

        """
        Called by our factory to send raw data to the client.

        Raw data is an object containing time and an integer reading which
        the client will plot in a chart.
        """

        values['ts'] = datetime.datetime.now().isoformat()
        self._send_message_dict('chart-data', values)


    def push_log_message(self, text):

        """
        Called by our factory to send log messages to the client.

        Log messages are objects with a single 'text' attribute and will be
        displayed by the client.
        """

        self._send_message_dict('log-message', {
            'message': text,
        })



class WSFactory(websocket.WebSocketServerFactory):

    """
    Twisted protocol factory for the server side websocket protocol.
    """

    protocol = WSProto

    def __init__(self, event_manager, *args, **kwargs):

        # Track a single `_connected_protocol` so that we can push data.

        super(WSFactory, self).__init__(*args, **kwargs)
        self._connected_protocol = None
        self.event_manager = event_manager

        event_manager.subscribe('arduino-raw', self._push_raw_data_to_client)
        event_manager.subscribe('log-message', self._push_log_msg_to_client)


    def set_active_protocol(self, active_proto):

        """
        Sets the protocol instance this factory will push data to.

        Drops any currenly active protocol connections to prevent concurrency.
        """

        if self._connected_protocol and self._connected_protocol != active_proto:
            self._connected_protocol.dropConnection()
        self._connected_protocol = active_proto


    def set_protocol_gone(self, gone_proto):

        """
        Clears the active protocol if it hasn't been changed in the meantime.
        """

        if self._connected_protocol != gone_proto:
            return
        self._connected_protocol = None


    def _push_raw_data_to_client(self, **values):

        """
        Sends raw `values` to the connected protocol, if any.
        """

        if self._connected_protocol:
            self._connected_protocol.push_raw_data(**values)


    def _push_log_msg_to_client(self, message):

        """
        Sends the log `message` to the connected protocol, if any.
        """

        if self._connected_protocol:
            self._connected_protocol.push_log_message(message)



def setup_websocket(reactor, event_manager):

    """
    Starts listening for websocket connections.
    """

    factory = WSFactory(event_manager)

    # TODO: Should port/interface be configurable? Client may need adjustments.
    reactor.listenTCP(8081, factory, interface='0.0.0.0')
    _log.info('listening for WSCK connections on 0.0.0.0:8081')


# ----------------------------------------------------------------------------
# webserver/websocket.py
# ----------------------------------------------------------------------------
