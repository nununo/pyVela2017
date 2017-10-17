#!/usr/bin/env python
# vim: ts=4:sw=4:et


import os
import random

from twisted.internet import task, defer, protocol
from twisted import logger

from txdbus import client as txdbus_client
from txdbus import interface as txdbus_interface



def sleep(seconds, reactor):

    d = defer.Deferred()
    reactor.callLater(seconds, d.callback, None)
    return d



class OMXPlayerDBusManager(object):

    def __init__(self, reactor, executable, extra_ld_lib_path=None):

        self.reactor = reactor
        self.executable = executable
        if extra_ld_lib_path is not None:
            ld_lib_path = os.environ.get('LD_LIBRARY_PATH', '')
            if ld_lib_path:
                new_ld_lib_path = '%s:%s' % (extra_ld_lib_path, ld_lib_path)
            else:
                new_ld_lib_path = extra_ld_lib_path
            os.environ['LD_LIBRARY_PATH'] = new_ld_lib_path

        self.log = logger.Logger(namespace='omx-dbus-mgr')
        self.name_prefix = 'com.example.player'

        self._dbus_conn = None
        self._player_names = set()
        self._players_starting = {}
        self._players_stopping = {}


    @property
    def dbus_conn(self):

        if self._dbus_conn is None:
            raise RuntimeError('Not connected to DBus.')
        return self._dbus_conn


    def generate_player_name(self):

        attempts = 256
        while attempts > 0:
            rand_name = '%s-%04x' % (self.name_prefix, random.getrandbits(16))
            if rand_name not in self._player_names:
                self._player_names.add(rand_name)
                break
            attempts -= 1
        else:
            raise ValueError('Failed generating name.')
        return rand_name


    @defer.inlineCallbacks
    def connect_to_dbus(self, bus_address='session'):

        self.log.info('connecting to dbus')
        self._dbus_conn = yield txdbus_client.connect(self.reactor, bus_address)
        self.log.info('connected to dbus')

        # Use this to track player DBus attachments.
        self.log.debug('getting org.freedesktop.DBus')
        dbus_obj = yield self.dbus_conn.getRemoteObject(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus'
        )
        self.log.debug('subscribing to NameOwnerChanged signal')
        yield dbus_obj.notifyOnSignal(
            'NameOwnerChanged',
            self._dbus_signal_name_owner_changed
        )
        self.log.debug('subscribed to NameOwnerChanged signal')


    def _dbus_signal_name_owner_changed(self, *args):

        self.log.debug('signal data={args}', args=args)
        player_name, old_addr, new_addr = args
        if not old_addr:
            tracking_dict = self._players_starting
        elif not new_addr:
            tracking_dict = self._players_stopping
        else:
            self.log.error('unexpected signal data')

        d = tracking_dict.get(player_name)
        if d:
            d.callback(player_name)


    def track_dbus_player(self, player_name):

        if player_name in self._players_starting:
            raise RuntimeError('Player %r already tracked.' % (player_name, ))

        self._players_starting[player_name] = defer.Deferred()
        self._players_stopping[player_name] = defer.Deferred()
        self.log.info('tracking dbus player {n!r}', n=player_name)


    @defer.inlineCallbacks
    def wait_dbus_player_start(self, player_name):

        try:
            self.log.info('waiting player {n!r} start', n=player_name)
            yield self._players_starting[player_name]
            self.log.info('player {n!r} started', n=player_name)
            del self._players_starting[player_name]
        except KeyError:
            raise RuntimeError('Player %r not tracked.' % (player_name,))


    @defer.inlineCallbacks
    def wait_dbus_player_stop(self, player_name):

        try:
            self.log.info('waiting player {n!r} stop', n=player_name)
            yield self._players_stopping[player_name]
            self.log.info('player {n!r} stopped', n=player_name)
            del self._players_stopping[player_name]
        except KeyError:
            raise RuntimeError('Player %r not tracked.' % (player_name,))



class _TrackStartStopProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, player_name):
        self.log = logger.Logger(namespace='%s-process-proto' % (player_name,))
        self.started = defer.Deferred()
        self.stopped = defer.Deferred()

    def makeConnection(self, process):
        self.log.debug('player process started')
        self.started.callback(process)

    def processEnded(self, reason):
        exit_code = reason.value.exitCode
        self.log.debug('player process ended; exit_code={ec!r}', ec=exit_code)
        self.stopped.callback(exit_code)



class OMXPlayer(object):

    def __init__(self, filename, dbus_mgr, *, layer=0, loop=False, alpha=255):

        self.filename = filename
        self.dbus_mgr = dbus_mgr
        self.layer = layer
        self.loop = loop
        self.alpha = alpha

        self.dbus_player_name = self.dbus_mgr.generate_player_name()
        self.log = logger.Logger(namespace=self.dbus_player_name)

        self._reactor = self.dbus_mgr.reactor
        self._dbus_conn = self.dbus_mgr.dbus_conn

        self._process_protocol = None
        self._process_transport = None
        self._dbus_player = None
        self._stop_in_progress = False


    def __repr__(self):

        return '<OMXPlayer %r filename=%r>' % (
            self.dbus_player_name,
            self.filename,
        )


    _OMX_DBUS_PLAYER_INTERFACE = txdbus_interface.DBusInterface(
        'org.mpris.MediaPlayer2.Player',
        txdbus_interface.Method('PlayPause', arguments='', returns=''),
        txdbus_interface.Method('Stop', arguments='', returns=''),
        txdbus_interface.Method('SetAlpha', arguments='ox', returns='x'),
        txdbus_interface.Method('Action', arguments='i', returns=''),
    )


    @defer.inlineCallbacks
    def spawn(self):

        player_name = self.dbus_player_name
        self.log.info('spawning player {p!r}', p=player_name)

        # Delegate helps us track child process DBus presence.
        self.dbus_mgr.track_dbus_player(player_name)

        # Spawn the omxplayer.bin process.
        self._process_protocol = _TrackStartStopProcessProtocol(player_name)
        args = [self.dbus_mgr.executable]
        if self.loop:
            args.append('--loop')
        args.extend(('--dbus_name', str(player_name)))
        args.extend(('--layer', str(self.layer)))
        args.extend(('--alpha', str(self.alpha)))
        args.append(str(self.filename))
        self._process_transport = self._reactor.spawnProcess(
            self._process_protocol,
            self.dbus_mgr.executable,
            args,
            env=None,
        )

        # Wait process protocol start confirmation.
        yield self._process_protocol.started

        # Wait until the player shows up on DBus.
        yield self.dbus_mgr.wait_dbus_player_start(player_name)

        # Get the DBus object for this player.
        self.log.debug('getting dbus player object')
        path = '/org/mpris/MediaPlayer2'
        ifaces = [
            'org.freedesktop.DBus.Properties',
            self._OMX_DBUS_PLAYER_INTERFACE,
        ]
        self._dbus_player = yield self._dbus_conn.getRemoteObject(
            player_name,
            path,
            interfaces=ifaces,
        )
        self.log.debug('got dbus player object')


    @defer.inlineCallbacks
    def stop(self, ignore_failures=False):

        player_name = self.dbus_player_name
        self.log.info('stopping player {p!r}', p=player_name)

        if not self._process_protocol.stopped.called:
            if not self._stop_in_progress:
                self._stop_in_progress = True
                self.log.debug('asking player to stop')
                try:
                    yield self._dbus_player.callRemote(
                        'Stop',
                        interface='org.mpris.MediaPlayer2.Player'
                    )
                except:
                    if not ignore_failures:
                        raise
                else:
                    self.log.debug('asked player to stop')

        # Wait until the process disappears from DBus.
        yield self.dbus_mgr.wait_dbus_player_stop(player_name)

        # Wait for the actual process to end and get exit code.
        exit_code = yield self._process_protocol.stopped
        defer.returnValue(exit_code)


    @defer.inlineCallbacks
    def play_pause(self):

        # Based on https://github.com/popcornmix/omxplayer
        self.log.debug('asking player to play/pause')
        yield self._dbus_player.callRemote(
            'PlayPause',
            interface='org.mpris.MediaPlayer2.Player'
        )
        self.log.debug('asked player to play/pause')


    @defer.inlineCallbacks
    def set_alpha(self, int64):

        self.log.debug('asking player to set alpha')
        result = yield self._dbus_player.callRemote(
            'SetAlpha', '/not/used', int64,
            interface='org.mpris.MediaPlayer2.Player'
        )
        self.log.debug('asked player to set alpha')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def action(self, int32):

        self.log.debug('asking player action')
        yield self._dbus_player.callRemote(
            'Action', int32,
            interface='org.mpris.MediaPlayer2.Player'
        )
        self.log.debug('asked player action')



if __name__ == '__main__':

    import sys

    from twisted.logger import (globalLogBeginner, textFileLogObserver,
        LogLevelFilterPredicate, FilteringLogObserver, LogLevel)


    def setup_logging(debug=False):

        observer = textFileLogObserver(sys.stderr, timeFormat='%H:%M:%S.%f')
        loglevel = LogLevel.debug if debug else LogLevel.info
        predicate = LogLevelFilterPredicate(defaultLogLevel=loglevel)
        predicate.setLogLevelForNamespace(
            'txdbus.client.DBusClientFactory',
            LogLevel.warn,
        )
        observers = [FilteringLogObserver(observer, [predicate])]
        globalLogBeginner.beginLoggingTo(observers)


    @defer.inlineCallbacks
    def start_things(reactor, settings):

        executable = settings['executable']
        ld_lib_path = settings['ld_lib_path']
        dbus_mgr = OMXPlayerDBusManager(reactor, executable, ld_lib_path)

        yield dbus_mgr.connect_to_dbus()

        player1 = OMXPlayer('./videos/0-00.mkv', dbus_mgr, layer=10)
        player2 = OMXPlayer('./videos/2-01.mkv', dbus_mgr, layer=20, alpha=0)
        player3 = OMXPlayer('./videos/3-01.mkv', dbus_mgr, layer=30, alpha=0)

        yield player1.spawn()

        yield sleep(5, reactor)

        yield player2.spawn()

        delay = 0.01
        for alpha in range(1, 256, 15):
            yield player2.set_alpha(alpha)
            yield sleep(delay, reactor)

        yield sleep(2, reactor)

        for alpha in range(254, -1, -15):
            yield player2.set_alpha(alpha)
            yield sleep(delay, reactor)

        yield player2.stop(ignore_failures=False)


        yield sleep(5, reactor)


        yield player3.spawn()

        delay = 0.01
        for alpha in range(1, 256, 15):
            yield player3.set_alpha(alpha)
            yield sleep(delay, reactor)

        yield sleep(4, reactor)

        for alpha in range(254, -1, -5):
            yield player3.set_alpha(alpha)
            yield sleep(delay, reactor)


        yield player3.stop(ignore_failures=False)

        yield sleep(5000, reactor)

        yield player1.stop(ignore_failures=False)


    _DBUS_ENV_VAR_NAME = 'DBUS_SESSION_BUS_ADDRESS'
    if _DBUS_ENV_VAR_NAME not in os.environ:
        print('%s not set. DBus session running?' % _DBUS_ENV_VAR_NAME)
        sys.exit(-1)

    SETTINGS = {
        'executable': '/usr/bin/omxplayer.bin',
        'ld_lib_path': '/usr/lib/omxplayer',
    }

    setup_logging(debug='-d' in sys.argv)
    task.react(start_things, (SETTINGS,))

