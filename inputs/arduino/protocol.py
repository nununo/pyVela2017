# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/protocol.py
# ----------------------------------------------------------------------------

"""
Low level, serial Arduino input protocol.
"""


from twisted.internet import protocol, defer
from twisted.protocols import basic
from twisted import logger



_log = logger.Logger(namespace='inputs.arduino')



class ArduinoProtocol(basic.LineReceiver):

    """
    Arduino serial connection protocol.
    """

    # The Arduino serial connection sends a stream of three-byte PDUs:
    # - The first byte is 0x20.
    # - The second and third bytes are a 16 bit little endian integer.

    # t.p.basic.LineReceiver handles this with the appropriate delimiter.
    # Not perfect but works:
    # - Arduino protocol uses delimiter as a "start of message" indicator.
    # - LineReceiver consideres delimiter to be "end of line" indicator.
    # Works because the Arduino keeps sending a stream of PDUs, never stopping.
    delimiter = b' '

    def __init__(self, pdu_received_callable):

        self._pdu_received_callable = pdu_received_callable
        self.disconnected = defer.Deferred()


    def connectionMade(self):

        # Called by Twisted when the serial connection is up.

        _log.debug('connection made')


    def lineReceived(self, line):

        # Called by Twisted when a PDU is received.
        # `line` should be a two byte little endian integer.

        _log.debug('data received: {d!r}', d=line)
        try:
            pdu = int.from_bytes(line, byteorder='little')
        except (TypeError, ValueError):
            _log.warn('bad value: {d!r}', d=line)
            return

        try:
            self._pdu_received_callable(pdu)
        except Exception as e:
            _log.warn('callable exception: {e!s}', e=e)


    def rawDataReceived(self, data):

        # Called by Twisted if the protocol goes to "raw" mode.
        # Should not happen, given that this code never triggers it.
        # It is here to ensure a complete protocol implementation, given that
        # the parent class does not implement it.

        _log.warn('unexpected data: {d!r}', d=data)


    def connectionLost(self, reason=protocol.connectionDone):

        # Called by Twisted when the serial connection is dropped.

        _log.debug('connection lost')
        self.disconnected.callback(None)


# ----------------------------------------------------------------------------
# inputs/arduino/protocol.py
# ----------------------------------------------------------------------------
