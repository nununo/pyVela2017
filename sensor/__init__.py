from twisted.internet import protocol, serialport

from twisted import logger



class _ArduinoProtocol(protocol.Protocol):

    def __init__(self, name):
        self._buffer = []
        self._log = logger.Logger(namespace='{}-arduino-proto'.format(name))

    def connectionMade(self):
        self._log.info('connection made')

    def dataReceived(self, data):
        self._log.debug('data received: {d!r}', d=data)
        self._buffer.append(data)
        self._processBuffer()

    def _isValidPDUBuffer(self, pduBuffer):
        return len(pduBuffer) == 2

    def _decodePDUBuffer(self, pduBuffer):
        return int.from_bytes(pduBuffer, byteorder='little')

    def _processBuffer(self):
        """
        Consume buffered bytes and fire self.pduReceived() for each valid PDU.
        """
        buffer  = b''.join(self._buffer)
        pduBuffers = buffer.split(b' ')
        for pduBuffer in pduBuffers:
            if self._isValidPDUBuffer(pduBuffer):
                pdu = self._decodePDUBuffer(pduBuffer)
                self.pduReceived(pdu)
        if pduBuffers and not self._isValidPDUBuffer(pduBuffers[-1]):
            self._buffer = [pduBuffers[-1]]
        
    def pduReceived(self, pdu):
        print('pdu received:', repr(pdu))

    def connectionLost(self, reason):
        self._log.info('connection lost')



def createSerialPort(reactor, deviceFilename, baudrate, name='default'):

    proto = _ArduinoProtocol(name)
    sp = serialport.SerialPort(proto, deviceFilename, reactor, baudrate=baudrate)
    return sp



if __name__ == '__main__':

    from twisted.internet import reactor

    DEVICE = '/dev/ttyACM0'
    BAUD = 9600
    
    sp = createSerialPort(reactor, DEVICE, BAUD)

    reactor.run()

