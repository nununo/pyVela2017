from .input import ArduinoInput


def initialize(player_manager, reactor, device_file, baud_rate):

    return ArduinoInput(player_manager, reactor, device_file, baud_rate)
