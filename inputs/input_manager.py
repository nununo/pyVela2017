
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

        network.initialize(self._player_mgr, self._reactor, port)


    def _create_input_arduino(self, device_file, baud_rate):

        arduino.initialize(self._player_mgr, self._reactor, device_file, baud_rate)

