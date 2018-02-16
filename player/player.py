# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/player.py
# ----------------------------------------------------------------------------

"""
Asyncronous, Twisted based, omxplayer process wrapper.
(see: https://github.com/popcornmix/omxplayer)
"""

import os
import random
from time import time

from twisted.internet import defer, protocol
from twisted import logger

from txdbus import error, interface as txdbus_interface


from .misc import sleep



class _TrackProcessProtocol(protocol.ProcessProtocol):

    """
    Twisted ProcessProtocol class used to track process startup/exit.
    Exposes two relevant attributes:
    - `started`: deferred that fires when the associated process is started.
    - `stopped`: deferred that fires when the associated process terminates.
    """

    def __init__(self, player_name):

        self.log = logger.Logger(namespace='player.proc.%s' % (player_name,))
        self.started = defer.Deferred()
        self.stopped = defer.Deferred()


    def connectionMade(self):

        # Called by Twisted when the process is started.

        self.log.info('player process started')
        self.started.callback(None)


    def outReceived(self, data):

        # Called by Twisted when the process writes to its standard output.

        self.log.debug('stdout: {s!r}', s=data)


    def errReceived(self, data):

        # Called by Twisted when the process writes to its standard error.

        self.log.warn('stderr: {s!r}', s=data)


    def processEnded(self, reason):

        # Called by Twisted when the process terminates.

        exit_code = reason.value.exitCode
        self.log.info('player process ended; exit_code={ec!r}', ec=exit_code)
        self.stopped.callback(exit_code)



class OMXPlayer(object):

    """
    Asyncronous, Twisted based, wrapper/proxy for omxplayer processes.
    """

    def __init__(self, filename, player_mgr, *, layer=0, loop=False, alpha=255,
                 fadein=0, fadeout=0):

        """
        Initialization arguments:
        - `filename`: the movie filename to play.
        - `player_mgr`: provides access to DBus, reactor, and more.
        - `layer`: used with omxplayer --layer argument.
        - `loop`: if true, omxplayer is passed the --loop argument.
        - `alpha`:  used with omxplayer --alpha argument.
        - `fadein`: fade in duration, in seconds.
        - `fadeout`: fade out duration, in seconds.
        """

        self.filename = filename
        self.player_mgr = player_mgr
        self.dbus_mgr = player_mgr.dbus_mgr
        self.layer = layer
        self.loop = loop
        self.alpha = alpha
        self._fadein = fadein
        self._fadeout = fadeout

        # Will be obtained by querying the omxplayer process via DBus.
        self._duration = None

        # Use a known name so that we can track omxplayer's DBus presence.
        self.dbus_player_name = self.generate_player_name(filename)
        self.log = logger.Logger(namespace='player.each.%s' % (self.dbus_player_name,))

        self._reactor = self.player_mgr.reactor
        self._dbus_conn = self.dbus_mgr.dbus_conn

        # Used to track omxplayer process startup/termination.
        self._process_protocol = None

        # TODO: Not really used, can go away.
        self._process_transport = None

        # DBus proxy object for the player: used to control it.
        self._dbus_player = None

        # Lifecycle tracking.
        self._ready = defer.Deferred()
        self._stop_in_progress = False


    def __repr__(self):

        return '<OMXPlayer %r filename=%r>' % (
            self.dbus_player_name,
            self.filename,
        )


    @staticmethod
    def generate_player_name(filename):
        """
        Generate unique player name.
        """
        return 'c.p%s-%s' % (
            os.path.splitext(os.path.basename(filename))[0],
            random.randint(10, 99),
        )


    # Maybe if txdbus and/or omxplayer's introspection abilities were better
    # these declarations wouldn't be needed; as of this writing, they are.

    # For the nitty gritty details, see:
    # - https://dbus.freedesktop.org/doc/dbus-specification.html
    # - https://github.com/popcornmix/omxplayer
    # - https://github.com/cocagne/txdbus

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

        """
        Spawns the omxplayer process associated to this instance, returning
        a deferred that fires after the process is started and ready to be
        controlled via the other instance methods; the spawned omxplayer
        will be paused.

        The optional `end_callable` will be called when the spawned omxplayer
        process terminates, and passed in a single argument with the omxplayer's
        exit code.
        """

        player_name = self.dbus_player_name
        self.log.info('spawning player {p!r}', p=player_name)

        # Ask DBus manager to track this player's name bus presence.
        self.dbus_mgr.track_dbus_name(player_name)

        self._spawn_process()

        # Wait for process started confirmation.
        yield self._process_protocol.started

        # Wait until the player name shows up on DBus.
        yield self.dbus_mgr.wait_dbus_name_start(player_name)

        # Setup the optional notification of process termination.
        if end_callable:
            self._process_protocol.stopped.addCallback(end_callable)

        yield self._get_dbus_player_object()

        yield self._get_duration()

        # Player is now ready to be controlled.
        self.log.info('player ready')
        self._ready.callback(None)

        # Since omxplayer defaults to starting in play mode, ask it to
        # play/pause straight away; we promised to have it paused when
        # done.
        yield self.play_pause()


    def _spawn_process(self):

        # Spawn the omxplayer.bin process.

        self._process_protocol = _TrackProcessProtocol(self.dbus_player_name)
        args = [self.player_mgr.executable]
        if self.loop:
            args.append('--loop')
        args.extend(('--dbus_name', str(self.dbus_player_name)))
        args.extend(('--layer', str(self.layer)))
        args.extend(('--orientation', str(180)))
        args.append('--no-osd')
        args.extend(('--alpha', str(self.alpha)))
        args.append(str(self.filename))

        # env=None, below, is relevant: it ensures that environment variables
        # this process has set are passed down to the child process; in this
        # case, PlayerManager probably set LD_LIBRARY_PATH.
        self._process_transport = self._reactor.spawnProcess(
            self._process_protocol,
            self.player_mgr.executable,
            args,
            env=None,
        )


    @defer.inlineCallbacks
    def _get_dbus_player_object(self):

        # Get the DBus object for this player.

        self.log.debug('getting dbus player object')

        # Hardcoded data from omxplayer documentation.
        ifaces = [
            self._OMX_DBUS_PLAYER_PROPERTIES,
            self._OMX_DBUS_PLAYER_INTERFACE,
        ]
        self._dbus_player = yield self._dbus_conn.getRemoteObject(
            self.dbus_player_name,
            '/org/mpris/MediaPlayer2',
            interfaces=ifaces,
        )
        self.log.debug('got dbus player object')


    @defer.inlineCallbacks
    def _get_duration(self):

        # Ask omxplayer for the duration of the video file.

        duration_microsecs = yield self._dbus_player.callRemote(
            'Get', 'org.mpris.MediaPlayer2.Player', 'Duration',
        )
        self._duration = duration_microsecs / 1000000
        self.log.debug('duration is {d}s', d=self._duration)


    @defer.inlineCallbacks
    def _wait_ready(self, action):

        # Returns a deferred that fires when the spawned omxplayer is
        # ready to be controlled via DBus; methods exposing such type of
        # controls will wait on this before issuing actual control commands
        # towards omxplayer; this prevents race conditions that exist between
        # the `spawn` method (that can take quite a while to complete) and
        # the remaining player control methods.

        # TODO: Convert this into a decorator?

        if not self._ready.called:
            self.log.info('wait ready: {a}', a=action)
        yield self._ready


    @defer.inlineCallbacks
    def stop(self, ignore_failures=False, timeout=1):

        """
        Requests the spawned omxplayer process to stop and exit.
        Returns a deferred that fires with the omxplayer process exit code.
        """

        player_name = self.dbus_player_name

        if self._process_protocol.stopped.called:
            # Prevent race condition: do nothing if process is gone.
            self.log.info('player already stopped {p!r}', p=player_name)
            exit_code = yield self._process_protocol.stopped
            defer.returnValue(exit_code)
            return

        yield self._wait_ready('stop')

        self.log.info('stopping player {p!r}', p=player_name)

        if not self._stop_in_progress:
            self._stop_in_progress = True
            self.log.debug('asking player to stop')
            try:
                # Prevent race condition with timeout: process might have
                # terminated in the meantime; timeout ensures we give up.
                yield self._dbus_player.callRemote(
                    'Stop',
                    interface='org.mpris.MediaPlayer2.Player',
                    timeout=timeout,
                )
            except error.TimeOut:
                # Assume the process is gone: we're done, but no exit code.
                self.log.info('player stop request timed out')
                exit_code = None
                defer.returnValue(exit_code)
                return
            except Exception as e:
                self.log.warn('stop request failed: {e!r}', e=e)
                if not ignore_failures:
                    raise
            else:
                self.log.debug('asked player to stop')

        if self._process_protocol.stopped.called:
            # Prevent race condition: do nothing if process is gone.
            self.log.info('player stopped in the meantime {p!r}', p=player_name)
            exit_code = yield self._process_protocol.stopped
            defer.returnValue(exit_code)
            return

        # Wait until the player name disappears from DBus.
        yield self.dbus_mgr.wait_dbus_name_stop(player_name)

        # Wait for the actual process to end and get exit code.
        exit_code = yield self._process_protocol.stopped
        defer.returnValue(exit_code)


    @defer.inlineCallbacks
    def play_pause(self):

        """
        Asks the spawned omxplayer to play/pause.
        Returns a deferred that fires once the command is acknowledged.
        """

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

        """
        To be used right after `spawn`, asks the spawned omxplayer to play.

        Immediately after that:
        - Schedules the video fade out, if not looping.
        - Initiates the video fade in.

        Returns a deferred that fires when the video as faded in completely.
        """

        yield self.play_pause()

        if not self.loop:
            delta_t = self._duration - self._fadeout - 0.1
            self._reactor.callLater(delta_t, self.fadeout)

        yield self.fadein()


    @defer.inlineCallbacks
    def _set_alpha(self, int64):

        """
        Asks the spawned omxplayer to change its alpha value.
        Returns a deferred that fires once the command is acknowledged.
        """

        result = yield self._dbus_player.callRemote(
            'SetAlpha', '/not/used', int64,
            interface='org.mpris.MediaPlayer2.Player'
        )
        defer.returnValue(result)


    @defer.inlineCallbacks
    def _fade(self, duration, from_alpha, to_alpha):

        # Issues timed calls to `_set_alpha` to ensure that the spawned
        # omxplayer's alpha is faded between the passed in alpha values:
        # - `duration` represents time in seconds.

        # Notes:
        # - Assumes 25fps video.
        # - Uses delay < 20ms which is 2x framerate.

        if duration:
            delay = 0.019
            start_time = time()
            delta_alpha = to_alpha - from_alpha
            relative_time = 0
            while relative_time < 1:
                alpha = from_alpha + delta_alpha * relative_time
                self.log.debug('alpha {s}', s=alpha)
                yield self._set_alpha(round(alpha))
                yield sleep(delay, self._reactor)
                relative_time = (time() - start_time) / duration

        result = yield self._set_alpha(round(to_alpha))
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadein(self):

        """
        Triggers a fade in of the spawned omxplayer.
        Returns a deferred that fires once the fade in is completed.
        """

        yield self._wait_ready('fade in')

        self.log.info('fade in starting')
        result = yield self._fade(self._fadein, 0, 255)
        self.log.info('fade in completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadeout(self):

        """
        Triggers a fade out of the spawned omxplayer.
        Returns a deferred that fires once the fade out is completed.
        """
        yield self._wait_ready('fade out')

        self.log.info('fade out starting')
        result = yield self._fade(self._fadeout, 255, 0)
        self.log.info('fade out completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def action(self, int32):

        """
        Triggers a generic omxplayer action.
        Returns a deferred that fires once the action is acknowledged.
        """
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
