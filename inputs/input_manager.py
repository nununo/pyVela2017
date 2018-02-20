# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------

"""
Asyncronous, Twisted based, input management.
"""

from . import network
from . import arduino



class InputManager(object):

    """
    Initializes inputs and mediates their feeds to a player manager.
    """

    def __init__(self, reactor, change_level_callable, raw_callable, settings):

        """
        Initializes configured inputs:
        - `reactor` is the Twisted reactor.
        - `change_level_callable` should trigger level changes when called.
        - `raw_callable` will be called by inputs with (source, value) raw data.
        - `settings` is a dict containing the 'inputs' key.
        """

        self._reactor = reactor
        self._change_level_callable = change_level_callable
        self._raw_callable = raw_callable

        self._inputs = []
        self._create_inputs(settings)


    def _create_inputs(self, settings):

        """
        Create each input configured in settings['inputs'].
        """

        for input_type, input_settings in settings['inputs'].items():
            try:
                method = getattr(self, '_create_input_%s' % (input_type,))
            except AttributeError:
                raise ValueError('invalid input type %r' % (input_type,))

            try:
                _input_object = method(**input_settings)
            except TypeError as e:
                raise ValueError('invalid %r setting: %s' % (input_type, e))


    def _create_input_network(self, port, interface='0.0.0.0'):

        network.initialize(
            self._reactor,
            port,
            interface,
            self._change_level_callable,
        )


    def _create_input_arduino(self, device_file, baud_rate, thresholds):

        arduino.initialize(
            self._reactor,
            device_file,
            baud_rate,
            thresholds,
            self._change_level_callable,
            self._raw_callable,
        )


# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------
