#!/usr/bin/env python
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

    player_manager = player.PlayerManager(reactor, settings)
    input_manager = inputs.InputManager(reactor, player_manager, settings)

    yield player_manager.start()
    yield player_manager.done



def main(argv, environ):

    dbus_env_var_name = 'DBUS_SESSION_BUS_ADDRESS'
    if dbus_env_var_name not in environ:
        print('%s not set. DBus session running?' % dbus_env_var_name)
        return -1

    log.setup(debug='-d' in argv)
    settings = load_settings()
    task.react(start_things, (settings,))

    return 0


if __name__ == '__main__':

    sys.exit(main(sys.argv, os.environ))


# ----------------------------------------------------------------------------
# main.py
# ----------------------------------------------------------------------------
