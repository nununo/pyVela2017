# ----------------------------------------------------------------------------
# player/misc.py
# ----------------------------------------------------------------------------

"""
Because Twisted does not include an asyncronous sleep function.
"""

from twisted.internet import defer


def sleep(seconds, reactor):
    """
    Returns a deferred that fires after `seconds` seconds.
    """
    d = defer.Deferred()
    reactor.callLater(seconds, d.callback, None)
    return d


# ----------------------------------------------------------------------------
# player/misc.py
# ----------------------------------------------------------------------------
