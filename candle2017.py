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

    # Twisted logger observer, will forward log messages to websockets.
    log_bridge = log.LogBridge()

    # Setup the logging system.
    log_level = settings.get('loglevel', 'warn')
    log_levels = settings.get('loglevels', {})
    log.setup(level=log_level, namespace_levels=log_levels,
              extra_observer=log_bridge)

    # Create the player manager.
    player_manager = player.PlayerManager(reactor, settings)

    # Start the HTTP and websocket servers.
    # `raw_listener` to be used to push raw data and logs to connected websockets.
    webserver.setup_webserver(reactor)
    raw_listener = webserver.setup_websocket(reactor, player_manager.level)

    # Create the input manager, wiring it to the player manager and `raw_listener`.
    # TODO: `_input_manager` not used, can go away.
    _input_manager = inputs.InputManager(
        reactor, player_manager, raw_listener, settings
    )

    # Connect the log bridge to the raw listener.
    log_bridge.destination = raw_listener

    # Read: start the player manager.
    yield player_manager.start()

    # Wait here until the player manager is done.
    yield player_manager.done



def respawn_under_dbus(settings):

    """
    Tries to respawn itself under a DBus session.
    """

    try:
        executable = settings['environment']['dbus_run_session_bin']
        os.execl(
            executable,
            executable,
            sys.executable,
            os.path.abspath(__file__),
        )
    except Exception as e:
        print('failed to execute %r: %s' % (executable, e))
        return False



def main(environ):

    """
    Main entry point.

    Loads settings, respawns under a DBus session if need and drives
    the main asynchronous code.
    """

    settings = load_settings()

    if 'DBUS_SESSION_BUS_ADDRESS' not in environ:
        if not respawn_under_dbus(settings):
            sys.exit(-1)

    task.react(start_things, (settings,))

    return 0


if __name__ == '__main__':

    sys.exit(main(os.environ))


# ----------------------------------------------------------------------------
# main.py
# ----------------------------------------------------------------------------
