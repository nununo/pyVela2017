# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------


from zope.interface import provider
from twisted.logger import ILogObserver, formatEvent



@provider(ILogObserver)
class LogBridge(object):

    def __init__(self):
        self.destination = None

    def __call__(self, event):
        if self.destination:
            msg = formatEvent(event)
            self.destination.log_message(msg)


# ----------------------------------------------------------------------------
# log/bridge.py
# ----------------------------------------------------------------------------
