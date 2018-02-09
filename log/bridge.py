# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------

"""
Helps bridging Twisted log messages towads runtime configurable destinations.
"""

from zope.interface import provider
from twisted.logger import ILogObserver, formatEvent



@provider(ILogObserver)
class LogBridge(object):

    """
    Twisted logger observer that forwards emitted logs towards a configurable
    `destination` object that should have a `log_message` method.
    """

    def __init__(self):

        # Where we'll forward log messages to.
        self.destination = None

    def __call__(self, event):

        # Called by Twisted to deliver a log event to this observer.

        # TODO: Convert `destination` into a simple callable?
        if self.destination:
            msg = formatEvent(event)
            self.destination.log_message(msg)


# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------
