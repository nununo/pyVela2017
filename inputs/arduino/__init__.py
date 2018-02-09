# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/arduino/__init__.py
# ----------------------------------------------------------------------------

"""
The serial based Arduino input.
"""

from .input import ArduinoInput


def initialize(input_manager, reactor, **kwargs):

    """
    Initializes the Arduino input.
    """

    return ArduinoInput(input_manager, reactor, **kwargs)


# ----------------------------------------------------------------------------
# inputs/arduino/__init__.py
# ----------------------------------------------------------------------------
