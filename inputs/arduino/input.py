# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------

"""
High level Arduino input.
"""

from collections import deque

from twisted.internet import defer
from twisted import logger

from inputs import input_base
from . import serial


_INPUT_SIZE = 25

_log = logger.Logger(namespace='inputs.arduino')



class ArduinoInput(input_base.InputBase):

    """
    Processes serial received PDUs (protocol data units) that are integers that
    will be bigger when the sensors detect "more wind".

    Keeps track of the last _INPUT_SIZE PDUs and calculates an aggregated
    derivative which is compared is compared to the given `thresholds` and,
    in turn, to fire `change_play_level` events via the `event_manager`.
    """

    def __init__(self, reactor, event_manager, device_file, baud_rate, thresholds):

        super(ArduinoInput, self).__init__(reactor, event_manager)
        self._device_file = device_file
        self._baud_rate = baud_rate
        self._thresholds = thresholds

        self._pdus = deque(maxlen=_INPUT_SIZE)
        self._last_play_level = 0

        self._serial_port = None


    @defer.inlineCallbacks
    def start(self):

        self._serial_port = serial.create_port(
            self._reactor,
            self._device_file,
            self._baud_rate,
            self._pdu_received,
        )
        _log.info('started: {d!r} open at {b} baud', d=self._device_file, b=self._baud_rate)
        yield defer.succeed(None)


    def _pdu_received(self, pdu):

        # The low level serial port code will call this where `pdu` is expected
        # to be an integer.

        # Keep track of this PDU and calculate the new aggregated derivative.
        self._pdus.append(pdu)
        _log.debug('pdus: {p!r}', p=self._pdus)
        agg_d = self._aggregated_derivative()
        _log.debug('aggregated derivative: {ad!r}', ad=agg_d)

        # Notify about the "raw data" we just received.
        self._event_manager.arduino_raw_data(raw=pdu, agd=agg_d)

        # Find if the aggregated derivative is over any of the thresholds and
        # request a level change, if that is the case.
        play_level = 0
        for level, threshold in enumerate(self._thresholds, start=1):
            if agg_d >= threshold:
                play_level = level
        if play_level != self._last_play_level:
            self._last_play_level = play_level
            self._event_manager.change_play_level(play_level, "arduino %r" % (agg_d,))


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
