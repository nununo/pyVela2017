# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# event/event_manager.py
# ----------------------------------------------------------------------------

"""
Simple callable based event manager.
"""

from __future__ import absolute_import

from . import event



class EventManager(object):

    """
    Callable based event manager with a minimal API.
    Summary:
    - Events are attributes of EventManager, created dynamically, as needed.
    - Events have zero or more handlers: functions/callables added to them.
    - Events are fired by calling them, like functions.
    - Firing an event calls all associated handlers, passing them the same
      arguments the "fire event" call was given.

    Usage example:

    >>> em = EventManager()

    # Tell the event manager to call our lambda when 'my_event' is fired.
    >>> em.my_event.calls(lambda: print('event handler #1'))

    # Adding another callable for 'my_event':
    >>> em.my_event.calls(lambda: print('event handler #2'))

    # Trigger 'my_event'
    >>> em.my_event()
    event handler #1
    event handler #2
    """

    def __init__(self):

        # Tracks known event objects:
        # - Keys are event names (my dynamic attributes).
        # - Values are Event objects.

        self._events = {}


    def __getattr__(self, name):

        # Called on attribute access, returns an event object.
        # Either uses an tracked one or creates new one, tracking it.

        try:
            return self._events[name]
        except KeyError:
            new_event = event.Event(name)
            self._events[name] = new_event
            return new_event


# ----------------------------------------------------------------------------
# event/event_manager.py
# ----------------------------------------------------------------------------
