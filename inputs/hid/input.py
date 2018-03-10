# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/hid/input.py
# ----------------------------------------------------------------------------

"""
The USB HID input.
"""


from twisted.internet import defer
from twisted import logger

from inputs import input_base
from . import reader



_log = logger.Logger(namespace='inputs.hid')



class USBHIDInput(input_base.InputBase):

    """
    USB HID input.

    Monitors USB HID events and delivers readings for the tracked event code.
    Operates at two levels:
    - Events are filtered and stored asynchronously, as they come.
    - The output stream of readings is kept at a constant pace, set by `period`,
      regardless of underlying events.
    """

    # The async storing of readings vs. steady-pace reading output production
    # has two benefits:
    # - It better integrates with the web based chart readings, behaving like
    #   other inputs (arduino and audio).
    # - It discards excessive readings that would bring unnecessary processing
    #   load to AGD with no benefits in responsiveness.

    def __init__(self, reactor, wiring, device_file, reading_event_code,
                 reading_scale=1, reading_offset=0, period=0.1):

        super(USBHIDInput, self).__init__(reactor, wiring)
        self._reading_scale = reading_scale
        self._reading_offset = reading_offset
        self._period = period

        # When started, calls `self._store_reading`, asynchronously, every
        # time an input event matching `reading_event_code` comes in.
        self._reader = reader.InputDeviceReader(
            reactor,
            device_file,
            reading_event_code,
            self._store_reading,
        )

        # The latest reading obtained from the `InputDeviceReader`.
        self._reading = None

        # Twisted DelayedCall used to generate periodic output.
        self._delayed_call = None


    @defer.inlineCallbacks
    def start(self):
        """
        Opens the input device and starts tracking events.
        Then initiates the periodic output.
        """
        self._reader.start()
        _log.info('started reading')
        self._send_reading_later()
        yield defer.succeed(None)


    def _store_reading(self, event):

        # Used as a callback to the InputDeviceReader.

        self._reading = event.value * self._reading_scale + self._reading_offset


    def _send_reading_later(self):

        # Produce output at a constant pace, every `self._period`.

        self._delayed_call = self._reactor.callLater(self._period, self._send_reading)


    def _send_reading(self):

        # Produce the actual output: unless there's none.

        reading = self._reading
        if reading is not None:
            self._wiring.hid(reading)

        # Self-schedule ourselves to run again, later.
        self._send_reading_later()


    @defer.inlineCallbacks
    def stop(self):
        """
        Stops reading from the input device and cancels periodic output.
        """
        yield self._reader.stop()
        if self._delayed_call:
            self._delayed_call.cancel()
        _log.info('stopped: no longer reading')


# ----------------------------------------------------------------------------
# inputs/hid/input.py
# ----------------------------------------------------------------------------
