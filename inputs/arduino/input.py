# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------

"""
High level Arduino input.
"""

from collections import deque

from twisted import logger

from . import serial


_INPUT_SIZE = 25

_log = logger.Logger(namespace='inputs.arduino')



class ArduinoInput(object):

    """
    Processes serial received PDUs (protocol data units) that are integers that
    will be bigger when the sensors detect "more wind".

    Keeps track of the last _INPUT_SIZE PDUs and calcualtes an aggregated
    derivative (see below).

    The aggregated derivative is compared to the given `thresholds` which, in
    turn, signals the `input_manager` for level changes.
    """

    def __init__(self, input_manager, reactor, device_file, baud_rate, thresholds):

        # TODO: Maybe replace the `input_manager` with a simple callable.
        self._input_manager = input_manager
        self._sp = serial.create_port(reactor, device_file, baud_rate, self._pdu_received)
        self._pdus = deque(maxlen=_INPUT_SIZE)
        self._thresholds = thresholds
        self._last_play_level = 0


    def _pdu_received(self, pdu):

        # The low level serial port code will call this where `pdu` is expected
        # to be an integer.

        # Tell the input manager about the "raw data" we just received.
        self._input_manager.raw(source="arduino", value=pdu)

        # Keep track of this PDU and calculate the new aggregated derivative.
        self._pdus.append(pdu)
        _log.debug('pdus: {p!r}', p=self._pdus)
        agg_d = self._aggregated_derivative()
        _log.debug('aggregated derivative: {ad!r}', ad=agg_d)

        # Find if the aggregated derivative is over any of the thresholds and
        # notify the input manager of a new level.
        play_level = 0
        for level, threshold in enumerate(self._thresholds, start=1):
            if agg_d >= threshold:
                play_level = level
        if play_level != self._last_play_level:
            self._last_play_level = play_level
            self._input_manager.level(play_level, "arduino %r" % (agg_d,))


    @staticmethod
    def _pairs_from(iterable):

        """
        Generates (i0, i1), (i1, i2), (i2, i3), ... tuples from `iterable`.
        """

        i = iter(iterable)
        try:
            one = next(i)
            while True:
                other = next(i)
                yield one, other
                one = other
        except StopIteration:
            pass


    def _aggregated_derivative(self):

        """
        Calculates the aggregated derivative of the last _INPUT_SIZE PDUs.
        Calculation:
        - Aggregates consecutive PDU deltas as long as they are >= 0.
        - If any consecutive PDU delta is negative, sets the aggregation to 0.
        """

        result = 0
        for one, next_one in self._pairs_from(self._pdus):
            derivative = next_one - one
            if derivative >= 0:
                result += derivative
            else:
                result = 0
        return result


# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------
