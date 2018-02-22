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
    Twisted logger observer firing `log_message` events for each emitted log.
    """

    def __init__(self, event_manager=None):

        # Used to fire `log_message` events.
        self._event_manager = event_manager

        # Tell the event manager not to use the logging system to report
        # event handling failures; otherwise, those would come back to to us.
        self._event_manager.log_message.use_log = None


    def __call__(self, event):

        # Called by Twisted to deliver a log event to this observer.
        # Details about `event` and more at:
        # http://twistedmatrix.com/documents/current/core/howto/logger.html

        # TODO: Maybe we don't need this any longer: remove condition?
        if self._event_manager:

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
            self._event_manager.log_message(msg)


# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------
