from .input import ArduinoInput


def initialize(player_manager, reactor, **kwargs):

    return ArduinoInput(player_manager, reactor, **kwargs)

