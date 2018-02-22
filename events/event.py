# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# event/event.py
# ----------------------------------------------------------------------------

"""
Simple callable based event.
"""

from __future__ import absolute_import

import sys

from twisted import logger



class Event(object):

    """
    Callable based event with a minimal API.
    Summary:
    - Has zero or more handlers: functions/callables added to it.
    - Fired by calling it, like a function.
    - Firing it calls all associated handlers, passing them any
      arguments given to call.
    """

    def __init__(self, name):

        self._name = name
        self._log = logger.Logger(namespace='events.%s' % (name,))

        # Handler functions/callables.
        self._functions = []


    def calls(self, function):

        """
        Adds `function` as a handler to this event.
        """

        self._functions.append(function)


    # There could be a "does_not_call" method to remove a known handler.


    def __call__(self, *args, log_failures=True, **kwargs):

        # Fires the event by calling all handler functions.

        # `log_failures` is used to prevent usage of the logging system:
        # This is necessary when a logging handler fires events (otherwise,
        # any exception here would trigger a log messages, that would trigger
        # an event, that would trigger a log messages, ad infinitum).

        for function in self._functions:
            try:
                function(*args, **kwargs)
            except Exception as e:
                # Catching exceptions here is critical to ensure decoupling
                # callables (firing events) from callees (handling events).

                # Try to produce a useful message including:
                # - The event name.
                # - The callable name.
                # - The raised execption.

                callable_name = getattr(function, '__qualname__', None)
                if callable_name is None:
                    callable_name = getattr(function, '__name__', 'non-named callable')

                msg = 'firing {ev!r} with {cn!r} failed: {e!r}'.format(
                    ev=self._name,
                    cn=callable_name,
                    e=e,
                )
                if log_failures:
                    self._log.error(msg)
                else:
                    sys.stderr.write(msg+'\n')


# ----------------------------------------------------------------------------
# event/event.py
# ----------------------------------------------------------------------------
