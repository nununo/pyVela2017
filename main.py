#!/usr/bin/env python
# vim: ts=4:sw=4:et

import os

from twisted.internet import task, defer

import player
import sensor
import utils


if __name__ == '__main__':

    import sys


    @defer.inlineCallbacks
    def start_things(reactor, settings):

        arduinoFIFO = defer.DeferredQueue()

        arduinoPort = sensor.createSerialPort(
            reactor,
            settings['deviceFilename'],
            settings['baudrate'],
            lambda value: arduinoFIFO.put(value),
        )


        player_manager = player.PlayerManager(reactor, settings)

        yield player_manager.start()
        yield player.sleep(5, reactor)
        yield player_manager.level(1)
        yield player.sleep(10, reactor)



    _DBUS_ENV_VAR_NAME = 'DBUS_SESSION_BUS_ADDRESS'
    if _DBUS_ENV_VAR_NAME not in os.environ:
        print('%s not set. DBus session running?' % _DBUS_ENV_VAR_NAME)
        sys.exit(-1)

    SETTINGS = {
        'executable': '/usr/bin/omxplayer.bin',
        'ld_lib_path': '/usr/lib/omxplayer',
        'deviceFilename': '/dev/ttyACM0',
        'baudrate': 9600,
    }

    utils.setup_logging(debug='-d' in sys.argv)
    task.react(start_things, (SETTINGS,))

