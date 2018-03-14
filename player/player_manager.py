# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/player_manager.py
# ----------------------------------------------------------------------------

"""
Asyncronous, Twisted based, video playing interface.
"""

import os
import random

from twisted.internet import defer
from twisted import logger

from .dbus_manager import DBusManager
from .player import OMXPlayer



class PlayerManager(object):

    """
    Tracks and controls video playing via one OMXPlayer instance per level.
    """

    # General lifecycle
    # -----------------
    # - Initialization finds available video files from the settings.
    # - Starting:
    #   - Spawns one OMXPlayer per level (which start in paused mode).
    #   - Unpause level 0 player.
    # - Level triggering calls (from the outside):
    #   - Unpause level X player.
    #   - Track player completion / process exit.
    #   - Respawn a new level X player.

    def __init__(self, reactor, wiring, settings):
        """
        Initializes the player manager:
        - `reactor` is the Twisted reactor.
        - `wiring` is used to register `change_play_level` handling.
        - `settings` is a dict with:
           - ['environment']['ld_library_path']
           - ['environment']['omxplayer_bin']
           - ['levels'][*]['folder']
           - ['levels'][*]['fadein']
           - ['levels'][*]['fadeout']
        """
        self.log = logger.Logger(namespace='player.mngr')

        self.reactor = reactor
        self._wiring = wiring
        self.settings = settings

        # part of our public interface, OMXPlayer will use this
        self.dbus_mgr = DBusManager(reactor, settings)

        # keys/values: integer levels/list of video files
        self.files = {}

        # keys/values: integer levels/OMXPlayer instances
        self.players = {}

        # the player currently running, if not level 0
        self._current_player = None

        self._update_ld_lib_path()
        self._find_files()

        self._stopping = False
        self.done = defer.Deferred()


    def _update_ld_lib_path(self):

        # Spawning omxplayer.bin requires associated shared libraries.
        # This updates/extends the LD_LIBRARY_PATH linux environment variable
        # such that those libraries can be found.

        extra_ld_lib_path = self.settings['environment']['ld_library_path']
        if extra_ld_lib_path:
            ld_lib_path = os.environ.get('LD_LIBRARY_PATH', '')
            if ld_lib_path:
                new_ld_lib_path = '%s:%s' % (extra_ld_lib_path, ld_lib_path)
            else:
                new_ld_lib_path = extra_ld_lib_path
            os.environ['LD_LIBRARY_PATH'] = new_ld_lib_path
            self.log.debug('LD_LIBRARY_PATH set to {v!r}', v=new_ld_lib_path)


    def _find_files(self):

        # Populate self.files by finding available files under each
        # level's configured folder in the settings dict.

        for level, level_info in self.settings['levels'].items():
            level_folder = level_info['folder']
            self.files[int(level)] = [
                os.path.join(level_folder, name)
                for name in os.listdir(level_folder)
            ]
        self.log.debug('files found: {d!r}', d=self.files)


    def _get_file_for_level(self, level):

        # Return a random filename from the available files in `level`.

        return random.sample(self.files[level], 1)[0]


    @property
    def executable(self):
        """
        Part of the public API, used by OMXPlayer.
        """
        return self.settings['environment']['omxplayer_bin']


    @defer.inlineCallbacks
    def start(self):
        """
        Spawns one player per level ensuring the level 0 one is playing.
        """
        self.log.info('starting')

        yield self.dbus_mgr.connect_to_dbus(disconnect_callable=self._dbus_disconnected)

        for level in self.files:
            yield self._create_player(level)

        yield self.players[0].play()

        # Ready to respond to change level requests.
        self._wiring.change_play_level.wire(self._change_play_level)

        self.log.info('started')


    @defer.inlineCallbacks
    def _dbus_disconnected(self):

        # Called by DBus manager when DBus connection is lost.

        if self._stopping:
            return

        self.log.warn('lost DBus connection: stopping')
        yield self.stop(skip_dbus=True)
        self.log.warn('lost DBus connection: stopped')


    @defer.inlineCallbacks
    def _create_player(self, level):

        # Spawns a player with a random video file for the given `level`.
        # Ensures:
        # - Level 0 players loop.
        # - Player end is tracked.

        self.log.info('creating player level={l!r}', l=level)
        player = OMXPlayer(
            self._get_file_for_level(level),
            self,
            layer=level,
            alpha=0,
            loop=(level == 0),
            fadein=self.settings['levels'][str(level)]['fadein'],
            fadeout=self.settings['levels'][str(level)]['fadeout'],
        )
        self.players[level] = player
        yield player.spawn(end_callable=lambda _: self._player_ended(player, level))


    def _change_play_level(self, new_level, comment=''):
        """
        Triggers video playing level change.
        Does nothing if:
        - Startup isn't completed.
        - `new_level` is less than or equal to the currently running level.
        """

        self.log.info('new_level={l!r} comment={c!r}', l=new_level, c=comment)

        if new_level == 0:
            self.log.info('will not go to rest ahead of time')
            return

        if self._current_player is self.players[3]:
            self.log.info('will not override level 3 player')
            return

        new_player = self.players.get(new_level)
        if new_player:
            new_player.play()
            if self._current_player:
                self.log.debug('smoothly stopping current player')
                self._current_player.fadeout_and_stop()
            else:
                self.log.debug('no current player to smoothly stop')
            self._current_player = new_player
            self.log.debug('current player updated')


    def _player_ended(self, player, level):

        # Called when a player for `level` ends (see _create_player), ensures
        # that new player is created such that it is ready when needed.

        self.log.info('player level={l!r} ended', l=level)
        if self._stopping:
            return
        self._create_player(level)
        if player is self._current_player:
            self.log.debug('current player set to none')
            self._current_player = None


    @defer.inlineCallbacks
    def stop(self, skip_dbus=False):
        """
        Asks all players to stop (IOW: terminate) and exits cleanly.
        """
        if self._stopping:
            return

        self.log.info('stopping')

        self._stopping = True
        self._wiring.change_play_level.unwire(self._change_play_level)
        for level, player in self.players.items():
            self.log.info('stopping player level={l!r}', l=level)
            yield player.stop(skip_dbus)
            self.log.info('stopped player level={l!r}', l=level)
        self.log.info('cleaning up dbus manager')
        yield self.dbus_mgr.cleanup()
        self.log.info('cleaned up dbus manager')

        self.log.info('stopped')
        self.done.callback(None)


# ----------------------------------------------------------------------------
# player/player_manager.py
# ----------------------------------------------------------------------------
