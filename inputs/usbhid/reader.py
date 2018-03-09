# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/usbhid/reader.py
# ----------------------------------------------------------------------------

"""
USB HID device reader.
"""


from twisted.internet import interfaces
from twisted import logger
from zope.interface import implementer


import evdev



_log = logger.Logger(namespace='inputs.usbhid.reader')



@implementer(interfaces.IReadDescriptor)
class InputDeviceReader(object):

    def __init__(self, reactor, device_file, event_name, negate, value_callback):

        self._reactor = reactor

        self._device = evdev.InputDevice(device_file)
        self._event_name = event_name
        self._negate = negate
        self._value_callback = value_callback


    def fileno(self):

        return self._device.fileno()


    def logPrefix(self):

        return 'InputDeviceReader(%r)' % (self._device,)


    def doRead(self):

        event = self._device.read_one()
        _log.debug('event: {e!r}', e=event)

        event_names = evdev.ecodes.bytype[event.type][event.code]
        if self._event_name in event_names:
            value = -event.value if self._negate else event.value
            _log.info('value {v!r}', v=value)
            self._value_callback(value)


    def connectionLost(self, reason):

        _log.warn('connection lost')
        self.stop()


    def start(self):

        self._device.grab()
        self._reactor.addReader(self)
        _log.info('started')


    def stop(self):

        self._reactor.removeReader(self)
        try:
            self._device.ungrab()
        except Exception as e:
            _log.warn('failed to ungrab device: {e!r}', e=e)
        _log.info('stopped')


# ----------------------------------------------------------------------------
# inputs/usbhid/reader.py
# ----------------------------------------------------------------------------
