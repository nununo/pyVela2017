# ----------------------------------------------------------------------------
# inputs/arduio/serial.py
# ----------------------------------------------------------------------------

from twisted.internet import protocol, serialport

from twisted import logger


_log = logger.Logger(namespace='arduino-serial')


class _ArduinoProtocol(protocol.Protocol):

    def __init__(self, pdu_received_callable):
        self._buffer = []
        self._log = logger.Logger(namespace='arduino-proto')
        self._pdu_received_callable = pdu_received_callable

    def connectionMade(self):
        self._log.info('connection made')

    def dataReceived(self, data):
        self._log.debug('data received: {d!r}', d=data)
        self._buffer.append(data)
        self._process_buffer()

    def _is_valid_pdu_buffer(self, pdu_buffer):
        return len(pdu_buffer) == 2

    def _decode_pdu_buffer(self, pdu_buffer):
        return int.from_bytes(pdu_buffer, byteorder='little')

    def _process_buffer(self):
        """
        Consume buffered bytes and fire self.pduReceived() for each valid PDU.
        """
        buffer = b''.join(self._buffer)
        pdu_buffers = buffer.split(b' ')
        for pdu_buffer in pdu_buffers:
            if self._is_valid_pdu_buffer(pdu_buffer):
                pdu = self._decode_pdu_buffer(pdu_buffer)
                try:
                    self._pdu_received_callable(pdu)
                except Exception as e:
                    self.log.warn('callable exception: {e!s}', e=e)
        if pdu_buffers and not self._is_valid_pdu_buffer(pdu_buffers[-1]):
            self._buffer = [pdu_buffers[-1]]

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

    sp = create_port(reactor, DEVICE, BAUD)

    reactor.run()


# ----------------------------------------------------------------------------
# inputs/arduio/serial.py
# ----------------------------------------------------------------------------
