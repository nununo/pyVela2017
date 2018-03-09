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

    def __init__(self, reactor, wiring, device_file, event_name, negate=False):

        super(USBHIDInput, self).__init__(reactor, wiring)
        self._device_file = device_file
        self._event_name = event_name

        self._reader = reader.InputDeviceReader(
            reactor,
            device_file,
            event_name,
            negate,
            wiring.usbhid,
        )


    @defer.inlineCallbacks
    def start(self):

        
        self._reader.start()
        _log.info('started: tracking {e!r}@{d}', e=self._event_name, d=self._device_file)
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def stop(self):

        yield self._reader.stop()
        _log.info('stopped: no longer reading')


# ----------------------------------------------------------------------------
# inputs/usbhid/input.py
# ----------------------------------------------------------------------------
