#!/usr/bin/env python
# vim: ts=4:sw=4:et


from twisted.internet import defer, protocol
from twisted import logger

from txdbus import interface as txdbus_interface



class _TrackStartStopProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, player_name):
        self.log = logger.Logger(namespace='%s-process-proto' % (player_name,))
        self.started = defer.Deferred()
        self.stopped = defer.Deferred()

    def makeConnection(self, process):
        self.log.debug('player process started')
        self.started.callback(process)

    def outReceived(self, data):
        self.log.debug('stdout: {s!r}', s=data)

    def errReceived(self, data):
        self.log.warn('stderr: {s!r}', s=data)

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

        self.dbus_player_name = self.dbus_mgr.generate_player_name(filename)
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


