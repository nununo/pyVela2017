#!/usr/bin/env python
# vim: ts=4:sw=4:et

from twisted.internet import defer
from twisted import logger

from .dbus_manager import OMXPlayerDBusManager
from .player import OMXPlayer
from .misc import sleep


class PlayerManager(object):

    def __init__(self, reactor, settings):

        self.log = logger.Logger(namespace='player-manager')
        self.reactor = reactor
        self.dbus_mgr = OMXPlayerDBusManager(
            reactor,
            settings['executable'],
            settings['ld_lib_path'],
        )

        self.base_player = None
        self.current_level = 0
        self.current_player = None


    @defer.inlineCallbacks
    def start(self):

        yield self.dbus_mgr.connect_to_dbus()
        self.base_player = OMXPlayer(
            '../videos/0-00.mkv',
            self.dbus_mgr,
            layer=10,
            loop=True,
        )
        yield self.base_player.spawn()


    @defer.inlineCallbacks
    def level(self, n):

        if n < self.current_level:
            return

        new_player = OMXPlayer('../videos/1-01.mkv', self.dbus_mgr, layer=20, fadein=1, fadeout=1)
        yield new_player.spawn(end_callable=lambda exit_code: self._player_ended(n))
        if self.current_player:
            yield self.current_player.stop()
        self.current_level = n
        self.current_player = new_player


    def _player_ended(self, level):

        self.log.info('player level={l!r} ended', l=level)
        self.current_level = 0
        self.current_player = None


    @defer.inlineCallbacks
    def stop(self):

        if self.current_player:
            self.log.info('stopping player level={l!r}', l=self.current_level)
            yield self.current_player.stop()
        self.log.info('stopping base player')
        yield self.base_player.stop()

