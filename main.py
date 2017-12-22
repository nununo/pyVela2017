#!/usr/bin/env python
# vim: ts=4:sw=4:et

from twisted.internet import task, defer

import player
import log
import inputs



@defer.inlineCallbacks
def start_things(reactor, settings):


    player_manager = player.PlayerManager(reactor, settings)
    input_manager = inputs.InputManager(reactor, player_manager, settings)

    yield player_manager.start()
    yield player_manager.done



if __name__ == '__main__':

    import json
    import os
    import sys


    _DBUS_ENV_VAR_NAME = 'DBUS_SESSION_BUS_ADDRESS'
    if _DBUS_ENV_VAR_NAME not in os.environ:
        print('%s not set. DBus session running?' % _DBUS_ENV_VAR_NAME)
        sys.exit(-1)


    # Load 'settings.json' from this file's directory.

    base_dir = os.path.dirname(os.path.abspath(__file__))
    settings_fname = os.path.join(base_dir, 'settings.json')

    with open(settings_fname, 'rt') as f:
        settings = json.loads(f.read())

    # Update relative paths in settings with this file's directory.
    for level_info in settings['levels'].values():
        level_info_folder = level_info['folder']
        if not os.path.isabs(level_info_folder):
            level_info['folder'] = os.path.abspath(
                os.path.join(base_dir, level_info_folder)
            )

    log.setup(debug='-d' in sys.argv)
    task.react(start_things, (settings,))

