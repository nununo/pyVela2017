# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# event/event_manager.py
# ----------------------------------------------------------------------------

"""
Simple callable based event manager.
"""

from __future__ import absolute_import

import collections
import sys

from twisted import logger



class EventManager(object):

    def __init__(self, name='events.mngr'):

        self._log = logger.Logger(namespace=name)
        self._subscriptions = collections.defaultdict(list)
        self._functions = {}


    def _event_functions(self, event):

        return self._subscriptions.get(event)


    def subscribe(self, event, function):

        self._subscriptions[event].append(function)


    def unsubscribe(self, event, function):

        functions = self._event_functions(event)
        try:
            functions.remove(function)
        except ValueError:
            pass


    def _fire(self, event, *args, log_failures=True, **kwargs):

        functions = self._event_functions(event)
        if not functions:
            return

        for function in functions:
            try:
                function(*args, **kwargs)
            except Exception as e:
                msg = 'firing {ev!r} failed: {e}'.format(ev=event, e=e)
                if log_failures:
                    self._log.error(msg)
                else:
                    sys.stderr.write(msg+'\n')


    def __getattr__(self, name):

        function = self._functions.get(name)
        if function:
            return function

        def function(*args, **kwargs):
            this_function = self._functions[name]
            self._fire(this_function, *args, **kwargs)

        self._functions[name] = function

        return function


# ----------------------------------------------------------------------------
# event/event_manager.py
# ----------------------------------------------------------------------------
