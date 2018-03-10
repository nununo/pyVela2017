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

from . import agd
from . import arduino
from . import audio
from . import network
from . import web
from . import hid



_log = logger.Logger(namespace='inputs')

_INPUT_CLASSES = {
    'agd': agd.Input,
    'arduino': arduino.Input,
    'audio': audio.Input,
    'hid': hid.Input,
    'network': network.Input,
    'web': web.Input,
}



class InputManager(object):

    """
    Initializes inputs and mediates their feeds to a player manager.
    """

    def __init__(self, reactor, wiring, settings):

        """
        Initializes the instance:
        - `reactor` is the Twisted reactor.
        - `wiring` usable by inputs to fire/handle event-like calls.
        - `settings` is a dict containing the 'inputs' key.
        """

        self._reactor = reactor
        self._wiring = wiring
        self._settings = settings

        self._inputs = []


    @defer.inlineCallbacks
    def start(self):

        """
        Instantiates and starts each configured input, returning a deferred that
        fires on completion.
        """

        _log.info('starting')
        for input_item in self._settings['inputs']:
            input_type = input_item.pop('type', None)
            enabled = input_item.pop('enabled', False)
            if not enabled:
                continue
            try:
                input_class = _INPUT_CLASSES[input_type]
            except KeyError:
                _log.error('invalid input type: {it!r}', it=input_type)
                raise
            try:
                input_obj = input_class(self._reactor, self._wiring, **input_item)
            except Exception as e:
                _log.error('bad {it!r} input settings {ii!r}: {e!r}',
                           it=input_type, ii=input_item, e=e)
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
