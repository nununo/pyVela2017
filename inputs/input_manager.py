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

    def __init__(self, reactor, event_manager, settings):

        """
        Initializes configured inputs:
        - `reactor` is the Twisted reactor.
        - `event_manager` # TODO: update this
        - `settings` is a dict containing the 'inputs' key.
        """

        self._reactor = reactor
        self._event_manager = event_manager

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
            self._event_manager,
        )


    def _create_input_arduino(self, device_file, baud_rate, thresholds):

        arduino.initialize(
            self._reactor,
            device_file,
            baud_rate,
            thresholds,
            self._event_manager,
        )


# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------
