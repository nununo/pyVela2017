# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------

"""
Asyncronous, Twisted based, input management.
"""

from twisted.internet import defer
from twisted import logger

from . import network
from . import arduino
from . import web



_log = logger.Logger(namespace='inputs')

_INPUT_CLASSES = {
    'network': network.Input,
    'arduino': arduino.Input,
    'web': web.Input,
}



class InputManager(object):

    """
    Initializes inputs and mediates their feeds to a player manager.
    """

    def __init__(self, reactor, event_manager, settings):

        """
        Initializes the instance:
        - `reactor` is the Twisted reactor.
        - `event_manager` usable by inputs to fire/handle events.
        - `settings` is a dict containing the 'inputs' key.
        """

        self._reactor = reactor
        self._event_manager = event_manager
        self._settings = settings

        self._inputs = []


    @defer.inlineCallbacks
    def start(self):

        """
        Instantiates and starts each configured input, returning a deferred that
        fires on completion.
        """

        _log.info('starting')
        for input_type, input_settings in self._settings['inputs'].items():
            try:
                input_class = _INPUT_CLASSES[input_type]
            except KeyError:
                _log.error('invalid input type: {it!r}', it=input_type)
                raise
            try:
                input_obj = input_class(self._reactor, self._event_manager, **input_settings)
            except Exception as e:
                _log.error('bad {it!r} input settings: {e!r}', it=input_type, e=e)
                raise
            try:
                yield input_obj.start()
            except Exception as e:
                _log.error('failed {it!r} input start: {e!r}', it=input_type, e=e)
                raise
            self._inputs.append((input_type, input_obj))
        _log.info('started')


    @defer.inlineCallbacks
    def stop(self):

        """
        Instantiates each configured input, returning a deferred that
        fires on completion.
        """

        _log.info('stopping inputs')
        for input_type, input_obj in self._inputs:
            try:
                yield input_obj.stop()
            except Exception as e:
                _log.error('failed input {it!r} stop: {e!r}', it=input_type, e=e)
        _log.info('stopped inputs')


# ----------------------------------------------------------------------------
# inputs/input_manager.py
# ----------------------------------------------------------------------------
