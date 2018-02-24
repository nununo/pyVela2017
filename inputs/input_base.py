# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/input_base.py
# ----------------------------------------------------------------------------

"""
Asyncronous, Twisted based, input base class module.
"""

from twisted.internet import defer



class InputBase(object):

    """
    Input base class.
    """

    def __init__(self, reactor, event_manager):

        """
        `reactor` is the Twisted reactor.
        `event_manager` used to fire/handle events.
        """

        self._reactor = reactor
        self._event_manager = event_manager


    @defer.inlineCallbacks
    def start(self):

        """
        Starts the input, returning a deferred that fires on completion.
        """

        raise NotImplementedError()


    @defer.inlineCallbacks
    def stop(self):

        """
        Stops the input, returning a deferred that fires on completion.
        """

        raise NotImplementedError()


# ----------------------------------------------------------------------------
# inputs/input_base.py
# ----------------------------------------------------------------------------
