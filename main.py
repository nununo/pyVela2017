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

        executable = settings['executable']
        ld_lib_path = settings['ld_lib_path']
        dbus_mgr = player.OMXPlayerDBusManager(reactor, executable, ld_lib_path)

        yield dbus_mgr.connect_to_dbus()

        p1 = player.OMXPlayer('../videos/0-00.mkv', dbus_mgr, layer=10)
        p2 = player.OMXPlayer('../videos/2-01.mkv', dbus_mgr, layer=20, alpha=0, fadein=0.5, fadeout=0.2)
#        p3 = player.OMXPlayer('../videos/3-01.mkv', dbus_mgr, layer=30, alpha=0, fadein=0.1, fadeout=1)

        yield p1.spawn()

        yield player.sleep(3, reactor)

        yield p2.spawn()
        yield p2.fadein()
        yield player.sleep(2, reactor)
        yield p2.fadeout()
        yield p2.stop(ignore_failures=False)

        yield player.sleep(5, reactor)


        yield p1.stop(ignore_failures=False)


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

