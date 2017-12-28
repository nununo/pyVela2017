#!/usr/bin/env python
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/player.py
# ----------------------------------------------------------------------------


from time import time


from twisted.internet import defer, protocol
from twisted import logger

from txdbus import interface as txdbus_interface


from .misc import sleep



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

    def __init__(self, filename, player_mgr, *, layer=0, loop=False, alpha=255,
                 fadein=0, fadeout=0):

        self.filename = filename
        self.player_mgr = player_mgr
        self.dbus_mgr = player_mgr.dbus_mgr
        self.layer = layer
        self.loop = loop
        self.alpha = alpha
        self._fadein = fadein
        self._fadeout = fadeout

        self._duration = None

        self.dbus_player_name = self.player_mgr.generate_player_name(filename)
        self.log = logger.Logger(namespace=self.dbus_player_name)

        self._reactor = self.player_mgr.reactor
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


    _OMX_DBUS_PLAYER_PROPERTIES = txdbus_interface.DBusInterface(
        'org.freedesktop.DBus.Properties',
        txdbus_interface.Method('Get', arguments='ss', returns='x'),
    )

    _OMX_DBUS_PLAYER_INTERFACE = txdbus_interface.DBusInterface(
        'org.mpris.MediaPlayer2.Player',
        txdbus_interface.Method('PlayPause', arguments='', returns=''),
        txdbus_interface.Method('Stop', arguments='', returns=''),
        txdbus_interface.Method('SetAlpha', arguments='ox', returns='x'),
        txdbus_interface.Method('Action', arguments='i', returns=''),
    )


    @defer.inlineCallbacks
    def spawn(self, end_callable=None):

        player_name = self.dbus_player_name
        self.log.info('spawning player {p!r}', p=player_name)

        # Delegate helps us track child process DBus presence.
        self.dbus_mgr.track_dbus_player(player_name)

        # Spawn the omxplayer.bin process.
        self._process_protocol = _TrackStartStopProcessProtocol(player_name)
        args = [self.player_mgr.executable]
        if self.loop:
            args.append('--loop')
        args.extend(('--dbus_name', str(player_name)))
        args.extend(('--layer', str(self.layer)))
        args.extend(('--alpha', str(self.alpha)))
        args.append(str(self.filename))
        self._process_transport = self._reactor.spawnProcess(
            self._process_protocol,
            self.player_mgr.executable,
            args,
            env=None,
        )

        # Wait process protocol start confirmation.
        yield self._process_protocol.started

        # Wait until the player shows up on DBus.
        yield self.dbus_mgr.wait_dbus_player_start(player_name)

        # Optional notification of process termination.
        if end_callable:
            self._process_protocol.stopped.addCallback(end_callable)

        # Get the DBus object for this player.
        self.log.debug('getting dbus player object')

        # Hardcoded data from OMXPlayer documentation.
        path = '/org/mpris/MediaPlayer2'
        ifaces = [
            self._OMX_DBUS_PLAYER_PROPERTIES,
            self._OMX_DBUS_PLAYER_INTERFACE,
        ]
        self._dbus_player = yield self._dbus_conn.getRemoteObject(
            player_name,
            path,
            interfaces=ifaces,
        )
        self.log.debug('got dbus player object')

        duration_microsecs = yield self._dbus_player.callRemote(
            'Get', 'org.mpris.MediaPlayer2.Player', 'Duration',
        )
        self._duration = duration_microsecs / 1000000
        self.log.info('duration is {d}s', d=self._duration)

        yield self.play_pause()


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
    def play(self):

        yield self.play_pause()

        if not self.loop:
            delta_t = self._duration - self._fadeout - 0.1
            self._reactor.callLater(delta_t, self.fadeout)

        yield self.fadein()


    @defer.inlineCallbacks
    def set_alpha(self, int64):

        result = yield self._dbus_player.callRemote(
            'SetAlpha', '/not/used', int64,
            interface='org.mpris.MediaPlayer2.Player'
        )
        defer.returnValue(result)


    # fadein/fadeout notes:
    # - assume 25fps
    # - attributes represent time in seconds
    # - use delay < 20ms which is 2x framerate

    @defer.inlineCallbacks
    def _fade(self, duration, from_, to_):

        if duration:
            delay = 0.019
            start_time = time()
            delta_alpha = to_ - from_
            relative_time = 0
            while relative_time < 1:
                alpha = from_ + delta_alpha * relative_time
                self.log.debug('alpha {s}', s=alpha)
                yield self.set_alpha(round(alpha))
                yield sleep(delay, self._reactor)
                relative_time = (time() - start_time) / duration

        result = yield self.set_alpha(round(to_))
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadein(self):

        self.log.info('fade in starting')
        result = yield self._fade(self._fadein, 0, 255)
        self.log.info('fade in completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadeout(self):

        self.log.info('fade out starting')
        result = yield self._fade(self._fadeout, 255, 0)
        self.log.info('fade out completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def action(self, int32):

        self.log.debug('asking player action')
        yield self._dbus_player.callRemote(
            'Action', int32,
            interface='org.mpris.MediaPlayer2.Player'
        )
        self.log.debug('asked player action')


# ----------------------------------------------------------------------------
# player/player.py
# ----------------------------------------------------------------------------
