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
from time import time

from twisted.internet import defer
from twisted import logger

from txdbus import error, interface as txdbus_interface

from common import process
from .misc import sleep



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

        self._filename = filename
        self._player_mgr = player_mgr
        self._dbus_mgr = player_mgr.dbus_mgr
        self._layer = layer
        self._loop = loop
        self._alpha = alpha
        self._fadein = fadein
        self._fadeout = fadeout

        # Will be obtained by querying the omxplayer process via DBus.
        self._duration = None

        # Use a known name so that we can track omxplayer's DBus presence.
        self._dbus_player_name = self.generate_player_name(filename)
        self._log = logger.Logger(namespace='player.each.%s' % (self._dbus_player_name,))

        self._reactor = self._player_mgr.reactor
        self._dbus_conn = self._dbus_mgr.dbus_conn

        # Used to track omxplayer process startup/termination.
        self._process_protocol = None

        # DBus proxy object for the player: used to control it.
        self._dbus_player = None

        # Lifecycle tracking.
        self._ready = defer.Deferred()
        self._stop_in_progress = False
        self._fadeout_dc = None
        self._fading_out = False


    def __repr__(self):

        return '<OMXPlayer %r filename=%r>' % (
            self._dbus_player_name,
            self._filename,
        )


    _player_id = 0

    @staticmethod
    def generate_player_name(filename):
        """
        Generate unique player name.
        """
        OMXPlayer._player_id = (OMXPlayer._player_id + 1) % 1000
        return 'c.p%s-%03i' % (
            os.path.splitext(os.path.basename(filename))[0],
            OMXPlayer._player_id,
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
        txdbus_interface.Method('SetPosition', arguments='ox', returns='x'),
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

        player_name = self._dbus_player_name
        self._log.info('spawning')

        # Ask DBus manager to track this player's name bus presence.
        self._dbus_mgr.track_dbus_name(player_name)

        self._spawn_process()

        # Wait for process started confirmation.
        yield self._process_protocol.started

        # Wait until the player name shows up on DBus.
        yield self._dbus_mgr.wait_dbus_name_start(player_name)

        # Setup the optional notification of process termination.
        if end_callable:
            self._process_protocol.stopped.addCallback(end_callable)

        yield self._get_dbus_player_object()

        yield self._determine_duration()

        # Player is now ready to be controlled.
        self._log.info('ready')
        self._ready.callback(None)

        # Since omxplayer defaults to starting in play mode, ask it to
        # play/pause straight away; we promised to have it paused when
        # done.
        yield self.play_pause()


    def _spawn_process(self):

        # Spawn the omxplayer.bin process.

        args = [self._player_mgr.executable]
        if self._loop:
            args.append('--loop')
        args.extend(('--dbus_name', str(self._dbus_player_name)))
        args.extend(('--layer', str(self._layer)))
        args.extend(('--orientation', str(180)))
        args.append('--no-osd')
        args.extend(('--alpha', str(self._alpha)))
        args.append(str(self._filename))

        self._process_protocol = process.spawn(
            self._reactor,
            args,
            'player.proc.%s' % (self._dbus_player_name,),
        )


    @defer.inlineCallbacks
    def _get_dbus_player_object(self):

        # Get the DBus object for this player.

        self._log.debug('getting dbus object')

        # Hardcoded data from omxplayer documentation.
        ifaces = [
            self._OMX_DBUS_PLAYER_PROPERTIES,
            self._OMX_DBUS_PLAYER_INTERFACE,
        ]
        self._dbus_player = yield self._dbus_conn.getRemoteObject(
            self._dbus_player_name,
            '/org/mpris/MediaPlayer2',
            interfaces=ifaces,
        )
        self._log.debug('got dbus object')


    @defer.inlineCallbacks
    def _determine_duration(self):

        # Ask omxplayer for the duration of the video file.

        duration_microsecs = yield self._dbus_player.callRemote(
            'Get', 'org.mpris.MediaPlayer2.Player', 'Duration',
        )
        self._duration = duration_microsecs / 1000000
        self._log.debug('duration is {d:.1f}s', d=self._duration)


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
            self._log.info('wait ready: {a}', a=action)
        yield self._ready


    @defer.inlineCallbacks
    def stop(self, skip_dbus=False, timeout=1):

        """
        Stops the spawned omxplayer process.

        If `skip_dbus` is False, starts by asking it to stop via DBus,
        waiting for it to cleanly stop.
        In that case, returns a deferred that fires with the exit code.

        If that fails, tries to send a SIGTERM signal to the process.
        If it works, waits for the process to cleanly stop.

        In the non DBus controlled clean stop, returns a deferred that fires
        with None, when completed.
        """

        player_name = self._dbus_player_name

        self._log.info('stopping')

        self._cancel_scheduled_fadeout()

        if self._process_protocol.stopped.called:
            # Prevent race condition: do nothing if process is gone.
            self._log.info('no process to stop', p=player_name)
            exit_code = yield self._process_protocol.stopped
            defer.returnValue(exit_code)
            return

        exit_code = None
        stop_via_sigterm = skip_dbus

        if not skip_dbus:
            try:
                exit_code = yield self._stop_via_dbus(timeout=timeout)
            except Exception as e:
                # May have failed due to timeout or any other reason.
                # The best we can do is ensuring we try stopping it via SIGTERM
                # and prevent exception propagation to caller, letting it assume
                # stop() completed successfully.
                stop_via_sigterm = True
                self._log.warn('stopping failed: {e!r}', e=e)

        if stop_via_sigterm:
            yield self._stop_via_sigterm()

        self._log.info('stopped')

        defer.returnValue(exit_code)


    @defer.inlineCallbacks
    def _stop_via_dbus(self, timeout):

        # Asks the spawned process to stop via a DBus command, waits
        # for it to be gone from DBus and for process exit. Returns a
        # deferred that fires with the process exit code.

        # May raise exceptions if, for example, DBus is unreachable.

        yield self._wait_ready('stop')

        if not self._stop_in_progress:
            self._stop_in_progress = True
            self._log.debug('requesting stop')
            try:
                # Prevent race condition with timeout: process might have
                # terminated or DBus may have become unreachable.
                yield self._dbus_player.callRemote(
                    'Stop',
                    interface='org.mpris.MediaPlayer2.Player',
                    timeout=timeout,
                )
            except error.TimeOut:
                self._log.info('stop request timed out')
                raise
            except Exception as e:
                self._log.warn('stop request failed: {e!r}', e=e)
                raise
            else:
                self._log.debug('requested stop')

        player_name = self._dbus_player_name

        if not self._process_protocol.stopped.called:
            # Process still there: wait until it disappears from DBus.
            yield self._dbus_mgr.wait_dbus_name_stop(player_name)

        # Finally, wait for the actual process to end and get exit code.
        exit_code = yield self._process_protocol.stopped
        defer.returnValue(exit_code)


    @defer.inlineCallbacks
    def _stop_via_sigterm(self):

        # Sends a SIGTERM to the spawned process and waits for it to exit.

        self._log.debug('signalling process termination')
        try:
            self._process_protocol.terminate()
        except OSError as e:
            self._log.warn('signalling process failed: {e!r}', e=e)
        else:
            self._log.debug('signalled process termination')

        # Finally, wait for the process to end, discarding the exit code.
        yield self._process_protocol.stopped


    @defer.inlineCallbacks
    def play_pause(self):

        """
        Asks the spawned omxplayer to play/pause.
        Returns a deferred that fires once the command is acknowledged.
        """

        yield self._wait_ready('play/pause')

        # Based on https://github.com/popcornmix/omxplayer
        self._log.debug('requesting play/pause')
        yield self._dbus_player.callRemote(
            'PlayPause',
            interface='org.mpris.MediaPlayer2.Player'
        )
        self._log.debug('requested play/pause')


    @defer.inlineCallbacks
    def play(self, skip_fadein=False):

        """
        To be used right after `spawn`, asks the spawned omxplayer to play.

        Immediately after that:
        - Schedules the video fade out, if not looping.
        - Initiates the video fade in.

        Returns a deferred that fires when the video as faded in completely.
        """

        yield self.play_pause()

        if not self._loop:
            self._schedule_fadeout()

        yield self.fadein(immediate=skip_fadein)


    def _schedule_fadeout(self):

        """
        Schedules end-of-video automatic fadeout.
        Assumes video has just started playing from the beginning.
        """

        self._cancel_scheduled_fadeout()

        delta_t = self._duration - self._fadeout - 0.1
        self._fadeout_dc = self._reactor.callLater(delta_t, self.fadeout)

        self._log.debug('will fade out in {d:.1f} seconds', d=delta_t)


    def _cancel_scheduled_fadeout(self):

        """
        Cancel any eventually scheduled fadeout.
        """

        if self._fadeout_dc:
            try:
                self._fadeout_dc.cancel()
            except Exception:
                pass


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
                self._log.debug('alpha {s}', s=alpha)
                yield self._set_alpha(round(alpha))
                yield sleep(delay, self._reactor)
                relative_time = (time() - start_time) / duration

        result = yield self._set_alpha(round(to_alpha))
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadein(self, immediate=False):

        """
        Triggers a fade in of the spawned omxplayer.
        Returns a deferred that fires once the fade in is completed.
        """

        yield self._wait_ready('fade in')

        self._log.info('fade in starting')
        result = yield self._fade(0 if immediate else self._fadein, 0, 255)
        self._log.info('fade in completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadeout(self):

        """
        Triggers a fade out of the spawned omxplayer.
        Returns a deferred that fires once the fade out is completed.
        """
        yield self._wait_ready('fade out')

        if self._fading_out:
            self._log.info('fade out in progress')
            return

        self._log.info('fade out starting')
        self._cancel_scheduled_fadeout()

        self._fading_out = True
        result = yield self._fade(self._fadeout, 255, 0)
        self._fading_out = False

        self._log.info('fade out completed')
        defer.returnValue(result)


    @defer.inlineCallbacks
    def fadeout_and_stop(self):

        """
        Stops after a fade out.
        """

        yield self.fadeout()
        yield self.stop()


# ----------------------------------------------------------------------------
# player/player.py
# ----------------------------------------------------------------------------
