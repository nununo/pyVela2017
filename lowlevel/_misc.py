
from twisted.internet import defer


def sleep(seconds, reactor):

    d = defer.Deferred()
    reactor.callLater(seconds, d.callback, None)
    return d

