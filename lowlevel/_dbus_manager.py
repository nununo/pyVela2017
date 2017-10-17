#!/usr/bin/env python
# vim: ts=4:sw=4:et


import os
import random

from twisted.internet import defer
from twisted import logger

from txdbus import client as txdbus_client



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



