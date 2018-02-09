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

from twisted import logger


_log = logger.Logger(namespace='inputs.arduino.serial')



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

        self._log = logger.Logger(namespace='inputs.arduino.proto')
        self._pdu_received_callable = pdu_received_callable


    def connectionMade(self):

        # Called by Twisted when the serial connection is up.

        self._log.info('connection made')


    def lineReceived(self, line):

        # Called by Twisted when a PDU is received.
        # `line` should be a two byte little endian integer.

        self._log.debug('data received: {d!r}', d=line)
        try:
            pdu = self._decode_pdu_buffer(line)
            self._pdu_received_callable(pdu)
        except Exception as e:
            self._log.warn('callable exception: {e!s}', e=e)


    def rawDataReceived(self, data):

        # Called by Twisted if the protocol goes to "raw" mode.
        # Should not happen, given that this code never triggers it.
        # It is here to ensure a complete protocol implementation, given that
        # the parent class does not implement it.

        self._log.warn('unexpected data: {d!r}', d=data)


    @staticmethod
    def _decode_pdu_buffer(pdu_buffer):

        # TODO: Throw this method away and inline it in `lineReceived`?

        return int.from_bytes(pdu_buffer, byteorder='little')


    def connectionLost(self, reason=protocol.connectionDone):

        # Called by Twisted when the serial connection is dropped.

        self._log.info('connection lost')



def create_port(reactor, device_filename, baudrate, pdu_received_callable):

    """
    Connects to the serial port given by `device_filename` at `baudrate`.

    Will call `pdu_received_callable` for each received PDU.
    """

    proto = _ArduinoProtocol(pdu_received_callable)
    try:
        port = serialport.SerialPort(proto, device_filename, reactor, baudrate=baudrate)
    except Exception as e:
        _log.warn('serial port opening failed: {f}', f=e)
        port = None
    return port


# ----------------------------------------------------------------------------
# inputs/arduio/serial.py
# ----------------------------------------------------------------------------
