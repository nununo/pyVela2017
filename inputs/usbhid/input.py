# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/usbhid/input.py
# ----------------------------------------------------------------------------

"""
The USB HID input.
"""


from twisted.internet import defer
from twisted import logger

from inputs import input_base
from . import reader



_log = logger.Logger(namespace='inputs.usbhid')



class USBHIDInput(input_base.InputBase):

    """
    USB HID input.

    Monitors USB HID events and delivers readings for the tracked event.
    """

    def __init__(self, reactor, wiring, device_file, reading_event_code,
                 reading_scale=1, reading_offset=0, period=0.1):

        super(USBHIDInput, self).__init__(reactor, wiring)
        self._reading_scale = reading_scale
        self._reading_offset = reading_offset
        self._period = period

        self._reader = reader.InputDeviceReader(
            reactor,
            device_file,
            reading_event_code,
            self._event_handler,
        )
        self._reading = None


    @defer.inlineCallbacks
    def start(self):

        self._reader.start()
        _log.info('started reading')
        self._send_reading_later()
        yield defer.succeed(None)


    def _event_handler(self, event):

        self._reading = event.value * self._reading_scale + self._reading_offset


    def _send_reading_later(self):

        self._delayed_call = self._reactor.callLater(self._period, self._send_reading)


    def _send_reading(self):

        value = self._reading
        if value is not None:
            self._wiring.usbhid(value)
        self._send_reading_later()


    @defer.inlineCallbacks
    def stop(self):

        yield self._reader.stop()
        _log.info('stopped: no longer reading')


# ----------------------------------------------------------------------------
# inputs/usbhid/input.py
# ----------------------------------------------------------------------------
