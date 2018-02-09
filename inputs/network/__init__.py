# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/network/__init__.py
# ----------------------------------------------------------------------------

"""
The TCP network connection input.
"""

from .protocol import ControlFactory


def initialize(input_manager, reactor, port, interface='0.0.0.0'):

    """
    Initializes the TCP input and starts listening for connections.
    """

    factory = ControlFactory(input_manager)
    reactor.listenTCP(port, factory, interface=interface)


# ----------------------------------------------------------------------------
# inputs/network/__init__.py
# ----------------------------------------------------------------------------
