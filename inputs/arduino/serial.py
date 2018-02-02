from twisted.internet import serialport
from twisted.protocols import basic

from twisted import logger


_log = logger.Logger(namespace='arduino-serial')


class _ArduinoProtocol(basic.LineReceiver):

    delimiter = b' '

    def __init__(self, pduReceivedCallable):
        self._log = logger.Logger(namespace='arduino-proto')
        self._pduReceivedCallable = pduReceivedCallable

    def connectionMade(self):
        self._log.info('connection made')

    def lineReceived(self, data):
        self._log.debug('data received: {d!r}', d=data)
        try:
            pdu = self._decodePDUBuffer(data)
            self._pduReceivedCallable(pdu)
        except Exception as e:
            self._log.warn('callable exception: {e!s}', e=e)

    def _decodePDUBuffer(self, pduBuffer):
        return int.from_bytes(pduBuffer, byteorder='little')

    def connectionLost(self, reason):
        self._log.info('connection lost')



def create_port(reactor, deviceFilename, baudrate, pduReceivedCallable):

    proto = _ArduinoProtocol(pduReceivedCallable)
    try:
        sp = serialport.SerialPort(proto, deviceFilename, reactor, baudrate=baudrate)
    except Exception as e:
        _log.warn('serial port opening failed: {f}', f=e)
        sp = None
    return sp



if __name__ == '__main__':

    from twisted.internet import reactor

    DEVICE = '/dev/ttyACM0'
    BAUD = 9600
    
    sp = create_port(reactor, DEVICE, BAUD)

    reactor.run()

