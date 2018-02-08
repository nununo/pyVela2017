# ----------------------------------------------------------------------------
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
        self.log = logger.Logger(namespace='player.proc.%s' % (player_name,))
        self.started = defer.Deferred()
        self.stopped = defer.Deferred()

    def connectionMade(self):
        self.log.info('player process started')
        self.started.callback(None)

    def outReceived(self, data):
        self.log.debug('stdout: {s!r}', s=data)

    def errReceived(self, data):
        self.log.warn('stderr: {s!r}', s=data)

    def processEnded(self, reason):
        exit_code = reason.value.exitCode
        self.log.info('player process ended; exit_code={ec!r}', ec=exit_code)
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
        self.log = logger.Logger(namespace='player.each.%s' % (self.dbus_player_name,))

        self._reactor = self.player_mgr.reactor
        self._dbus_conn = self.dbus_mgr.dbus_conn

        self._process_protocol = None
        self._process_transport = None
        self._dbus_player = None
        self._stop_in_progress = False
        self._ready = defer.Deferred()


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
        self.dbus_mgr.track_dbus_name(player_name)

        # Spawn the omxplayer.bin process.
        self._process_protocol = _TrackStartStopProcessProtocol(player_name)
        args = [self.player_mgr.executable]
        if self.loop:
            args.append('--loop')
        args.extend(('--dbus_name', str(player_name)))
        args.extend(('--layer', str(self.layer)))
        args.extend(('--orientation', str(180)))
        args.append('--no-osd')
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
        yield self.dbus_mgr.wait_dbus_name_start(player_name)

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

        # now ready to be controlled
        self.log.info('player ready')
        self._ready.callback(None)

        yield self.play_pause()


    @defer.inlineCallbacks
    def _wait_ready(self, action):

        if not self._ready.called:
            self.log.info('wait ready: {a}', a=action)
        yield self._ready


    @defer.inlineCallbacks
    def stop(self, ignore_failures=False):

        yield self._wait_ready('stop')

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
                except Exception:
                    if not ignore_failures:
                        raise
                else:
                    self.log.debug('asked player to stop')

        # Wait until the player disappears from DBus.
        yield self.dbus_mgr.wait_dbus_name_stop(player_name)

        # Wait for the actual process to end and get exit code.
        exit_code = yield self._process_protocol.stopped
        defer.returnValue(exit_code)


    @defer.inlineCallbacks
    def play_pause(self):

        yield self._wait_ready('play/pause')

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
    def _set_alpha(self, int64):

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
                yield self._set_alpha(round(alpha))
                yield sleep(delay, self._reactor)
                relative_time = (time() - start_time) / duration

        result = yield self._set_alpha(round(to_))
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadein(self):

        yield self._wait_ready('fade in')

        self.log.info('fade in starting')
        result = yield self._fade(self._fadein, 0, 255)
        self.log.info('fade in completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadeout(self):

        yield self._wait_ready('fade out')

        self.log.info('fade out starting')
        result = yield self._fade(self._fadeout, 255, 0)
        self.log.info('fade out completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def action(self, int32):

        yield self._wait_ready('action')

        self.log.debug('asking player action')
        yield self._dbus_player.callRemote(
            'Action', int32,
            interface='org.mpris.MediaPlayer2.Player'
        )
        self.log.debug('asked player action')


# ----------------------------------------------------------------------------
# player/player.py
# ----------------------------------------------------------------------------
