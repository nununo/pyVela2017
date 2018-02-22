#!/usr/bin/env python
# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# main.py
# ----------------------------------------------------------------------------

"""
Vela2017 entry point.
"""

import json
import os
import sys

from twisted.internet import task, defer

import events
import player
import log
import inputs
import webserver



def load_settings(filename='settings.json'):

    """
    Returns a dict from the `filename` JSON contents.

    Updates the relative paths under levels.*.folder to absolute paths, assuming
    them to be relative to this module's directory.
    """

    # Load from this file's directory.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    settings_fname = os.path.join(base_dir, filename)

    with open(settings_fname, 'rt') as f:
        settings = json.loads(f.read())

    # Update relative paths in settings with this file's directory.
    for level_info in settings['levels'].values():
        level_info_folder = level_info['folder']
        if not os.path.isabs(level_info_folder):
            level_info['folder'] = os.path.abspath(
                os.path.join(base_dir, level_info_folder)
            )

    return settings



@defer.inlineCallbacks
def start_things(reactor, settings):

    """
    Asyncronous, Twisted based, main code.

    Sets up all needed objects, some dependent on the `settings` configuration
    dict, and starts the player manager.

    Exits when the player manager terminates.
    """

    # Decouples callers from callees, who "subscribe" to events "fired" by callers.
    event_manager = events.EventManager()

    # Twisted logger observer: fires `log_message` events.
    log_bridge = log.LogBridge(event_manager)

    # Setup the logging system.
    log_level = settings.get('loglevel', 'warn')
    log_levels = settings.get('loglevels', {})
    log.setup(level=log_level, namespace_levels=log_levels, extra_observer=log_bridge)

    # Tell the event manager what to do with `set_log_level` events.
    event_manager.set_log_level.calls(log.set_level)


    # Create the player manager.
    player_manager = player.PlayerManager(reactor, event_manager, settings)


    # Start the HTTP and websocket servers.
    webserver.setup_webserver(reactor)
    webserver.setup_websocket(reactor, event_manager)


    # Create the input manager.
    # TODO: `_input_manager` either goes away or is used on exit/cleanup.
    _input_manager = inputs.InputManager(reactor, event_manager, settings)


    # Ensure a clean stop.
    reactor.addSystemEventTrigger('before', 'shutdown', stop_things, player_manager)


    # Start the player manager.
    try:
        yield player_manager.start()
    except Exception:
        # May fail at launching child processes, logs should help diagnose.
        raise SystemExit(-1)

    # Not done until the player manager is done.
    yield player_manager.done



@defer.inlineCallbacks
def stop_things(player_manager):

    """
    Asyncronous, Twisted based, cleanup.

    Asks the player manage to stop which, in turn, will stop the spawned player
    processes.
    """

    yield player_manager.stop()



def main():

    """
    Main entry point.

    Loads settings, and drives the main asynchronous code.
    """

    settings = load_settings()
    task.react(start_things, (settings,))



if __name__ == '__main__':

    sys.exit(main())


# ----------------------------------------------------------------------------
# main.py
# ----------------------------------------------------------------------------
