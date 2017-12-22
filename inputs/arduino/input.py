
from twisted import logger

from . import serial


_log = logger.Logger(namespace='arduino-input')


class ArduinoInput(object):

    def __init__(self, player_manager, reactor, device_file, baud_rate):

        self._sp = serial.create_port(reactor, device_file, baud_rate, self._pdu_received)


    def _pdu_received(self, pdu):

        _log.info('pdu={pdu!r}', pdu=pdu)

