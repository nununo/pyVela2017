# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/hid/reader.py
# ----------------------------------------------------------------------------

"""
USB HID device reader.
"""


from twisted.internet import interfaces
from twisted import logger
from zope.interface import implementer


import evdev



_log = logger.Logger(namespace='inputs.hid.reader')



@implementer(interfaces.IReadDescriptor)
class InputDeviceReader(object):

    """
    Twisted IReadDescritor implementation that reads events from the USB HID
    HID device file, integrating evdev's InputDevice file descriptor into the
    reactor and using the InputDevice's read_one() method.

    Events matching `reading_event_code` will be passed to the `event_callback`.
    """

    def __init__(self, reactor, device_file, reading_event_code, event_callback):

        self._reactor = reactor

        self._device = evdev.InputDevice(device_file)
        self._reading_event_code = reading_event_code
        self._event_callback = event_callback


    def fileno(self):
        """
        Twisted requires this to return the open UNIX file descriptor.
        """
        return self._device.fileno()


    def logPrefix(self):
        """
        Twisted uses this to generate log messages.
        """
        return 'InputDeviceReader(%r)' % (self._device,)


    def doRead(self):
        """
        Called by Twisted when the UNIX file descriptor as data for reading.
        """
        event = self._device.read_one()
        _log.debug('event: {e!r}', e=event)

        event_codes = evdev.ecodes.bytype[event.type][event.code]
        if self._reading_event_code in event_codes:
            self._event_callback(event)


    def connectionLost(self, reason):
        """
        Called by Twisted when the file descriptor is closed or becomes unavailable.
        """
        _log.warn('connection lost: {r!r}', r=reason)
        self.stop()


    def start(self):
        """
        Tell Twisted to start tracking the UNIX file descriptor for reading.
        """
        self._device.grab()
        self._reactor.addReader(self)
        _log.info('started')


    def stop(self):
        """
        Tell Twisted to stop tracking the UNIX file descriptor for reading.
        """
        self._reactor.removeReader(self)
        try:
            self._device.ungrab()
        except Exception as e:
            _log.warn('failed to ungrab device: {e!r}', e=e)
        _log.info('stopped')


# ----------------------------------------------------------------------------
# inputs/hid/reader.py
# ----------------------------------------------------------------------------
