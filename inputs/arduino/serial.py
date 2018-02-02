from twisted.internet import protocol, serialport

from twisted import logger


_log = logger.Logger(namespace='arduino-serial')


class _ArduinoProtocol(protocol.Protocol):

    def __init__(self, pduReceivedCallable):
        self._buffer = []
        self._log = logger.Logger(namespace='arduino-proto')
        self._pduReceivedCallable = pduReceivedCallable

    def connectionMade(self):
        self._log.info('connection made')

    def dataReceived(self, data):
        self._log.debug('data received: {d!r}', d=data)
        self._buffer.append(data)
        self._processBuffer()

    def _decodePDUBuffer(self, pduBuffer):
        return int.from_bytes(pduBuffer, byteorder='little')

    def _processBuffer(self):
        """
        Consume buffered bytes and fire self.pduReceived() for each valid PDU.
        """
        self._log.debug('process buffer start: buffer={b!r}', b=b''.join(self._buffer))
        buffer  = b''.join(self._buffer)
        wait_marker = True
        bytes_pending = 0
        pdu_buffer = b''
        last_consumed_byte = 0
        pdu = None
        for i, byte in enumerate(buffer):
            if byte == 32:
                if not wait_marker:
                    self._log.warn('unexpected space marker')
                wait_marker = False
                bytes_pending = 2
                pdu_buffer = b''
            else:
                if bytes_pending <= 0:
                    self._log.warn('unexpected data byte {b!r}', b=byte)
                pdu_buffer += bytes((byte,))
                bytes_pending -= 1
                if bytes_pending == 0:
                    pdu = self._decodePDUBuffer(pdu_buffer)
                    last_consumed_byte = i
                    wait_marker = True
        if pdu:
            try:
                self._pduReceivedCallable(pdu)
            except Exception as e:
                self.log.warn('callable exception: {e!s}', e=e)
            self._buffer = [buffer[last_consumed_byte+1:]]
        self._log.debug('process buffer done: buffer={b!r}', b=b''.join(self._buffer))

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

