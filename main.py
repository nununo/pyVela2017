#!/usr/bin/env python
# vim: ts=4:sw=4:et

import os

from twisted.internet import task, defer

from player import OMXPlayerDBusManager, OMXPlayer, sleep
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

        executable = settings['executable']
        ld_lib_path = settings['ld_lib_path']
        dbus_mgr = OMXPlayerDBusManager(reactor, executable, ld_lib_path)

        yield dbus_mgr.connect_to_dbus()

        player1 = OMXPlayer('../videos/0-00.mkv', dbus_mgr, layer=10)
        player2 = OMXPlayer('../videos/2-01.mkv', dbus_mgr, layer=20, alpha=0, fadein=0.5, fadeout=0.2)
#        player3 = OMXPlayer('../videos/3-01.mkv', dbus_mgr, layer=30, alpha=0, fadein=0.1, fadeout=1)

        yield player1.spawn()

        yield sleep(3, reactor)

        yield player2.spawn()
        yield player2.fadein()
        yield sleep(2, reactor)
        yield player2.fadeout()
        yield player2.stop(ignore_failures=False)

        yield sleep(5, reactor)


        yield player1.stop(ignore_failures=False)


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

