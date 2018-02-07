# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# main.py
# ----------------------------------------------------------------------------

import json
import os
import sys

from twisted.internet import task, defer

import player
import log
import inputs
import webserver


def load_settings(filename='settings.json'):

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

    log_bridge = log.LogBridge()

    log_level = settings.get('loglevel', 'warn')
    log_levels = settings.get('loglevels', {})
    log.setup(level=log_level, namespace_levels=log_levels,
              extra_observer=log_bridge)

    webserver.setup_webserver(reactor)
    raw_listener = webserver.setup_websocket(reactor)
    player_manager = player.PlayerManager(reactor, settings)
    _input_manager = inputs.InputManager(
        reactor, player_manager, raw_listener, settings
    )

    log_bridge.destination = raw_listener

    yield player_manager.start()
    yield player_manager.done



def main(environ):

    dbus_env_var_name = 'DBUS_SESSION_BUS_ADDRESS'
    if dbus_env_var_name not in environ:
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
