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

    # Start the HTTP and websocket servers.
    # `raw_listener` to be used to push raw data and logs to connected websockets.
    webserver.setup_webserver(reactor)
    raw_listener = webserver.setup_websocket(reactor)

    # Create the player manager.
    player_manager = player.PlayerManager(reactor, settings)

    # Create the input manager, wiring it to the player manager and `raw_listener`.
    _input_manager = inputs.InputManager(
        reactor, player_manager, raw_listener, settings
    )

    # Connect the log bridge to the raw listener.
    log_bridge.destination = raw_listener

    # Read: start the player manager.
    yield player_manager.start()

    # Wait here until the player manager is done.
    yield player_manager.done



def main(environ):

    """
    Main entry point.

    If not running under a DBus session prints a message and exits.
    Otherwise, loads the settings and drives the main asynchronous code.
    """

    dbus_env_var_name = 'DBUS_SESSION_BUS_ADDRESS'
    if dbus_env_var_name not in environ:
        # TODO: Respawn ourselves under a spawned private DBus session?
        print('%s not set. DBus session running?' % dbus_env_var_name)
        return -1

    settings = load_settings()
    task.react(start_things, (settings,))

    return 0


if __name__ == '__main__':

    sys.exit(main(os.environ))


# ----------------------------------------------------------------------------
# main.py
# ----------------------------------------------------------------------------
