# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/serial.py
# ----------------------------------------------------------------------------

"""
Low level, serial Arduino input.
"""

from twisted.internet import serialport, protocol
from twisted.protocols import basic

from . common import log



class _ArduinoProtocol(basic.LineReceiver):

    # The Arduino serial connections sends a stream of three-byte PDUs:
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


    def connectionMade(self):

        # Called by Twisted when the serial connection is up.

        log.debug('connection made')


    def lineReceived(self, line):

        # Called by Twisted when a PDU is received.
        # `line` should be a two byte little endian integer.

        log.debug('data received: {d!r}', d=line)
        try:
            pdu = int.from_bytes(line, byteorder='little')
        except (TypeError, ValueError):
            log.warn('bad value: {d!r}', d=line)
            return

        try:
            self._pdu_received_callable(pdu)
        except Exception as e:
            log.warn('callable exception: {e!s}', e=e)


    def rawDataReceived(self, data):

        # Called by Twisted if the protocol goes to "raw" mode.
        # Should not happen, given that this code never triggers it.
        # It is here to ensure a complete protocol implementation, given that
        # the parent class does not implement it.

        log.warn('unexpected data: {d!r}', d=data)


    def connectionLost(self, reason=protocol.connectionDone):

        # Called by Twisted when the serial connection is dropped.

        log.debug('connection lost')



def create_port(reactor, device_filename, baudrate, pdu_received_callable):

    """
    Connects to the serial port given by `device_filename` at `baudrate`.

    Will call `pdu_received_callable` for each received PDU.
    """

    proto = _ArduinoProtocol(pdu_received_callable)
    try:
        port = serialport.SerialPort(proto, device_filename, reactor, baudrate=baudrate)
    except Exception as e:
        log.warn('serial port opening failed: {f}', f=e)
        port = None
    return port


# ----------------------------------------------------------------------------
# inputs/arduio/serial.py
# ----------------------------------------------------------------------------
