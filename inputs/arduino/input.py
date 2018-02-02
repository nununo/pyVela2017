# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------

from collections import deque

from twisted import logger

from . import serial


_INPUT_SIZE = 10

_log = logger.Logger(namespace='arduino-input')


class ArduinoInput(object):

    def __init__(self, player_manager, reactor, device_file, baud_rate, thresholds):

        self._player_manager = player_manager
        self._sp = serial.create_port(reactor, device_file, baud_rate, self._pdu_received)
        self._pdus = deque(maxlen=_INPUT_SIZE)
        self._thresholds = thresholds
        self._last_play_level = 0


    def _pdu_received(self, pdu):

        self._pdus.append(pdu)
        _log.debug('pdus: {p!r}', p=self._pdus)
        agg_d = self._aggregated_derivative()
        _log.debug('aggregated derivative: {ad!r}', ad=agg_d)
        play_level = 0
        for level, threshold in enumerate(self._thresholds, start=1):
            if agg_d >= threshold:
                play_level = level
        if play_level != self._last_play_level:
            self._last_play_level = play_level
            self._player_manager.level(play_level)


    def _pairs_from(self, thing):
        i = iter(thing)
        one = next(i)
        while True:
            other = next(i)
            yield one, other
            one = other

    def _aggregated_derivative(self):

        result = 0
        for one, next in self._pairs_from(self._pdus):
            derivative = next - one
            if derivative >= 0:
                result += derivative
            else:
                result = 0
        return result


# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------
