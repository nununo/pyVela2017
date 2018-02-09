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

    def __init__(self, reactor, player_manager, raw_listener, settings):

        """
        Initializes configured inputs:
        - `reactor` is the Twisted reactor.
        - `player_manager` should have `level` method to trigger level changes.
        - `raw_listener` should a `raw` method to trigger raw input data handling.
        - `settings` is a dict containing the 'inputs' key.
        """

        # TODO: Maybe `player_manager` and `raw_listener` could be replaced with
        # callables instead of objects with a given interface.

        self._reactor = reactor
        self._player_mgr = player_manager
        self._raw_listener = raw_listener
        self._settings = settings

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


    def _create_input_network(self, port):

        network.initialize(self, self._reactor, port)


    def _create_input_arduino(self, **kwargs):

        arduino.initialize(self, self._reactor, **kwargs)


    def level(self, level, comment):

        """
        Inputs will call this, which will be forwarded to the player manager.
        """

        self._player_mgr.level(level, comment)


    def raw(self, source, value):

        """
        Inputs will call this, which will be forwarded to the raw listener.
        """

        self._raw_listener.raw(source, value)


# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------
