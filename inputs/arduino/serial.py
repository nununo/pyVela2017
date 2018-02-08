# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/serial.py
# ----------------------------------------------------------------------------

from twisted.internet import serialport, protocol
from twisted.protocols import basic

from twisted import logger


_log = logger.Logger(namespace='inputs.arduino.serial')



class _ArduinoProtocol(basic.LineReceiver):

    delimiter = b' '

    def __init__(self, pdu_received_callable):
        self._log = logger.Logger(namespace='inputs.arduino.proto')
        self._pdu_received_callable = pdu_received_callable

    def connectionMade(self):
        self._log.info('connection made')

    def lineReceived(self, line):
        self._log.debug('data received: {d!r}', d=line)
        try:
            pdu = self._decode_pdu_buffer(line)
            self._pdu_received_callable(pdu)
        except Exception as e:
            self._log.warn('callable exception: {e!s}', e=e)

    def rawDataReceived(self, data):
        self._log.warn('unexpected data: {d!r}', d=data)

    @staticmethod
    def _decode_pdu_buffer(pdu_buffer):
        return int.from_bytes(pdu_buffer, byteorder='little')

    def connectionLost(self, reason=protocol.connectionDone):
        self._log.info('connection lost')



def create_port(reactor, device_filename, baudrate, pdu_received_callable):

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
