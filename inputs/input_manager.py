# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------

from . import network
from . import arduino


class InputManager(object):

    def __init__(self, reactor, player_manager, settings):

        self._reactor = reactor
        self._player_mgr = player_manager
        self._settings = settings

        self._inputs = []
        self._create_inputs(settings)


    def _create_inputs(self, settings):

        for input_type, input_settings in settings['inputs'].items():
            try:
                method = getattr(self, '_create_input_%s' % (input_type,))
            except AttributeError:
                raise ValueError('invalid input type %r' % (input_type,))

            try:
                input_object = method(**input_settings)
            except TypeError as e:
                raise ValueError('invalid %r setting: %s' % (input_type, e))


    def _create_input_network(self, port):

        network.initialize(self, self._reactor, port)


    def _create_input_arduino(self, **kwargs):

        arduino.initialize(self, self._reactor, **kwargs)


    def level(self, level, comment):

        self._player_mgr.level(level, comment)


    def raw(self, *args):

        pass

# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------
