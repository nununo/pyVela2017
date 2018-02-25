# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------

"""
High level Arduino input.
"""


from twisted.internet import defer, serialport
from twisted import logger

from inputs import input_base
from . import protocol



_INPUT_SIZE = 25



_log = logger.Logger(namespace='inputs.arduino')




class ArduinoInput(input_base.InputBase):

    """
    Processes serial received PDUs (protocol data units) that are integers that
    will be bigger when the sensors detect "more wind".

    Produces output by firing `arduino` events via the `event_manager`.
    """

    def __init__(self, reactor, event_manager, device_file, baud_rate):

        super(ArduinoInput, self).__init__(reactor, event_manager)
        self._device_file = device_file
        self._baud_rate = baud_rate
        self._output_callable = event_manager.arduino

        self._serial_protocol = None
        self._serial_port = None


    @defer.inlineCallbacks
    def start(self):

        self._serial_protocol = protocol.ArduinoProtocol(self._output_callable)
        try:
            self._serial_port = serialport.SerialPort(
                self._serial_protocol,
                self._device_file,
                self._reactor,
                baudrate=self._baud_rate,
            )
        except Exception as e:
            _log.warn('serial port opening failed: {f}', f=e)
            raise
        _log.info(
            'started: {d!r} open at {b} baud',
            d=self._device_file,
            b=self._baud_rate,
        )
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def stop(self):

        _log.debug('stopping')

        # Signal the serial port for disconnection...
        self._serial_port.loseConnection()

        # ...then wait on the protocol for the confirmation.
        disconnected_deferred = self._serial_protocol.disconnected
        disconnected_deferred.addTimeout(5, self._reactor)
        try:
            yield disconnected_deferred
        except Exception as e:
            _log.warn('stopping failed: {e!r}', e=e)
        else:
            _log.info('stopped')


# ----------------------------------------------------------------------------
# inputs/arduino/input.py
# ----------------------------------------------------------------------------
