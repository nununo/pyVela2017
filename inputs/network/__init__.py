from .protocol import ControlFactory


def initialize(player_manager, reactor, port, interface='0.0.0.0'):

    factory = ControlFactory(player_manager)
    reactor.listenTCP(port, factory, interface=interface)
