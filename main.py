#!/usr/bin/env python
# vim: ts=4:sw=4:et

from twisted.internet import task, defer

import player
import sensor
import utils
import network



@defer.inlineCallbacks
def start_things(reactor, settings):

    arduinoFIFO = defer.DeferredQueue()

    arduinoPort = sensor.createSerialPort(
        reactor,
        settings['arduino']['device_file'],
        settings['arduino']['baud_rate'],
        lambda value: arduinoFIFO.put(value),
    )


    player_manager = player.PlayerManager(reactor, settings)

    f = network.ControlFactory(player_manager)
    reactor.listenTCP(10000, f, interface='0.0.0.0')


    yield player_manager.start()
    yield player.sleep(3, reactor)
    yield player_manager.level(1)
    yield player.sleep(500, reactor)
    yield player_manager.stop()



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

    utils.setup_logging(debug='-d' in sys.argv)
    task.react(start_things, (settings,))

