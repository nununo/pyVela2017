# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------

"""
Helps bridging Twisted log messages towads runtime configurable destinations.
"""

from datetime import datetime

from zope.interface import provider
from twisted import logger



@provider(logger.ILogObserver)
class LogBridge(object):

    """
    Twisted logger observer that forwards emitted logs to a callable, accepting
    a string as its single argument.
    """

    def __init__(self, destination_callable=None):

        # Where we'll forward log messages to.
        self.destination_callable = destination_callable


    def __call__(self, event):

        # Called by Twisted to deliver a log event to this observer.
        # Details about `event` and more at:
        # http://twistedmatrix.com/documents/current/core/howto/logger.html

        if self.destination_callable:

            # Formatted messages contain four elements, space separated:
            # - Fixed width, capitalized first letter of log level.
            # - Fixed width, seconds and milliseconds of event timestamp.
            # - Variable width, logger namespace.
            # - Variable width, formatted message itself.

            log_datetime = datetime.fromtimestamp(event['log_time'])
            msg = '%s %s %s %s' % (
                event['log_level'].name[0].upper(),
                log_datetime.strftime('%S.%f')[:6],
                event.get('log_namespace', '-'),
                logger.formatEvent(event),
            )
            self.destination_callable(msg)


# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------
