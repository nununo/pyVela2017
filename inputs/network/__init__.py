# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/network/__init__.py
# ----------------------------------------------------------------------------

from .protocol import ControlFactory


def initialize(player_manager, reactor, port, interface='0.0.0.0'):

    factory = ControlFactory(player_manager)
    reactor.listenTCP(port, factory, interface=interface)


# ----------------------------------------------------------------------------
# inputs/network/__init__.py
# ----------------------------------------------------------------------------
