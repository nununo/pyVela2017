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
    Twisted logger observer that forwards emitted logs towards a configurable
    `destination` object that should have a `log_message` method.
    """

    def __init__(self):

        # Where we'll forward log messages to.
        self.destination = None

    def __call__(self, event):

        # Called by Twisted to deliver a log event to this observer.
        # Details about `event` and more at:
        # http://twistedmatrix.com/documents/current/core/howto/logger.html

        # TODO: Convert `destination` into a simple callable?
        if self.destination:
            # Formatted messages contain four elements, space separated:
            # - Capitalized first letter of log level.
            # - Seconds and milliseconds of event timestamp.
            # - The logger namespace (variable width).
            # - The formatted log message itself.
            log_datetime = datetime.fromtimestamp(event['log_time'])
            msg = '%s %s %s %s' % (
                event['log_level'].name[0].upper(),
                log_datetime.strftime('%S.%f')[:6],
                event.get('log_namespace', '-'),
                logger.formatEvent(event),
            )
            self.destination.log_message(msg)


# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------
