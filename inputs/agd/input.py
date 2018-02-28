# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/agd/input.py
# ----------------------------------------------------------------------------

"""
Aggregated derivative input processor.
"""


from collections import deque

from twisted.internet import defer
from twisted import logger

from inputs import input_base



_log = logger.Logger(namespace='inputs.agd')




class AggregatedDerivative(input_base.InputBase):

    """
    Aggregated derivative input processor.

    Keeps track of the last `buffer_size` readings and calculates an aggregated
    derivative which is compared to the given `thresholds` and, in turn, calls
    `change_play_level` on the `wiring`.
    """

    def __init__(self, reactor, wiring, buffer_size, thresholds, source):

        super(AggregatedDerivative, self).__init__(reactor, wiring)

        self._wiring = wiring
        self._thresholds = thresholds
        self._source_name = source

        # TODO: wires should allow "wiring.wire[source].calls_to(...)"
        getattr(wiring.wire, source).calls_to(self._input_received)

        self._agd = 0
        self._derivatives = deque(maxlen=buffer_size)
        self._buffer_size = buffer_size
        self._last_reading = None
        self._last_play_level = 0

        # Notify of current thresholds: web client will use this.
        for level, value in enumerate(thresholds, start=1):
            wiring.notify_agd_threshold(level, value)

        # Wire threshold change requests to ourselves.
        wiring.wire.set_agd_threshold.calls_to(self._set_threshold)


    @defer.inlineCallbacks
    def start(self):

        _log.info('started')
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def stop(self):

        _log.info('stopped')
        yield defer.succeed(None)


    def _set_threshold(self, level, value):

        try:
            self._thresholds[level-1] = value
        except IndexError:
            _log.warn('invalid threshold level: {l!r}', l=level)
        else:
            _log.info('threshold level {l!r} set to {v!r}', l=level, v=value)
            self._wiring.notify_agd_threshold(level, value)



    def _input_received(self, reading):

        _log.info('reading={r!r}', r=reading)

        self._update_aggregated_derivative(reading)
        agd = self._agd

        # Output both the raw reading as well as the aggregated derivative.
        self._wiring.agd_output(raw=reading, agd=agd)

        # Find if the aggregated derivative is over any of the thresholds and
        # request a level change, if that is the case.
        play_level = 0
        for level, threshold in enumerate(self._thresholds, start=1):
            if agd >= threshold:
                play_level = level
        if play_level != self._last_play_level:
            self._last_play_level = play_level
            source_name = 'agd-%s == %r' % (self._source_name, agd)
            self._wiring.change_play_level(play_level, source_name)


    def _update_aggregated_derivative(self, reading):

        """
        Updates the aggregated derivative based on the current state:
        - Aggregated derivative.
        - Current and previous readings.
        - Last known, up to `buffer_size`, derivatives.
        """

        # NOTE
        # ----
        # This is a computationally optimized version of AGD calculation.
        # It is equivalent to:
        # - Starting off with AGD = 0.
        # - Keeping track of `buffer_size` readings.
        # - Aggregating buffered reading derivatives, in order such that:
        #   - If a derivative is >=0 add it to AGD.
        #   - Otherwise, set AGD to 0.

        derivative_count = len(self._derivatives)
        if not derivative_count and self._last_reading is None:
            # No stored derivatives, no _last reading.
            self._last_reading = reading
            return

        # We know the last reading and thus determine the derivative.
        derivative = reading - self._last_reading
        self._last_reading = reading

        if derivative < 0:
            # Rule: negative derivative clears everything.
            self._agd = 0
            self._derivatives.clear()
            return

        if derivative_count < self._buffer_size:
            # Derivative "buffer" not full, just aggregate the derivative.
            self._agd += derivative
            self._derivatives.append(derivative)
        else:
            # Derivative buffer full: aggregate derivative minus oldest one.
            oldest_derivative = self._derivatives[0]
            self._agd += derivative - oldest_derivative
            self._derivatives.append(derivative)


# ----------------------------------------------------------------------------
# inputs/agd/input.py
# ----------------------------------------------------------------------------
