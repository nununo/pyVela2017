from twisted.internet import serialport
from twisted.protocols import basic

from twisted import logger


_log = logger.Logger(namespace='arduino-serial')


class _ArduinoProtocol(basic.LineReceiver):

    delimiter = b' '

    def __init__(self, pdu_received_callable):
        self._log = logger.Logger(namespace='arduino-proto')
        self._pdu_received_callable = pdu_received_callable

    def connectionMade(self):
        self._log.info('connection made')

    def lineReceived(self, data):
        self._log.debug('data received: {d!r}', d=data)
        try:
            pdu = self._decode_pdu_buffer(data)
            self._pdu_received_callable(pdu)
        except Exception as e:
            self._log.warn('callable exception: {e!s}', e=e)

    def _decode_pdu_buffer(self, pdu_buffer):
        return int.from_bytes(pdu_buffer, byteorder='little')

    def connectionLost(self, reason):
        self._log.info('connection lost')



def create_port(reactor, device_filename, baudrate, pdu_received_callable):

    proto = _ArduinoProtocol(pdu_received_callable)
    try:
        sp = serialport.SerialPort(proto, device_filename, reactor, baudrate=baudrate)
    except Exception as e:
        _log.warn('serial port opening failed: {f}', f=e)
        sp = None
    return sp



if __name__ == '__main__':

    from twisted.internet import reactor

    DEVICE = '/dev/ttyACM0'
    BAUD = 9600

    sp = create_port(reactor, DEVICE, BAUD, lambda pdu: print('pdu: %r' % (pdu,)))

    reactor.run()


# ----------------------------------------------------------------------------
# inputs/arduio/serial.py
# ----------------------------------------------------------------------------
