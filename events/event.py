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

        # See `_log_handler_failure` below.
        self.use_log = True

        # Handler functions/callables.
        self._functions = []


    def calls(self, function):

        """
        Adds `function` as a handler to this event.
        """

        self._functions.append(function)


    # There could be a "does_not_call" method to remove a known handler.


    def __call__(self, *args, **kwargs):

        # Fires the event by calling all handler functions.

        for function in self._functions:
            try:
                function(*args, **kwargs)
            except Exception as e:
                # Catching exceptions here is critical to ensure decoupling
                # callables (firing events) from callees (handling events).
                self._log_handler_failure(function, e)


    def _log_handler_failure(self, function, e):

        # Try to produce a useful message including:
        # - The event name.
        # - The callable name.
        # - The raised execption.

        # `self.use_log` is used to prevent usage of the logging system:
        # This is necessary when a logging handler fires events (otherwise,
        # any exception here would trigger a log messages, that would trigger
        # an event, that would trigger a log messages, ad infinitum).
        #
        # Possible values:
        # - True or truthy: logging system will be used.
        # - None: Not output will be produced.
        # - False or falsey: outputs to sys.stderr.
        #   (beware: logging system may capture stderr, None may be needed!)

        handler_name = self._handler_name(function)
        msg = 'firing {hn!r} failed: {e!r}'.format(hn=handler_name, e=e)
        if self.use_log:
            self._log.error(msg)
        elif self.use_log is not None:
            sys.stderr.write('events.'+self._name+': '+msg+'\n')


    def _handler_name(self, function):

        # Return the best possible name for the function.
        # Will be formatted like "module_name.function_name".

        function_name = getattr(function, '__qualname__', None)
        if function_name is None:
            # Older Python versions to not support __qualname__.
            function_name = getattr(function, '__name__', 'non-named-callable')

        module_name = getattr(function, '__module__', 'non-named-module')

        return '%s.%s' % (module_name, function_name)


# ----------------------------------------------------------------------------
# event/event.py
# ----------------------------------------------------------------------------
