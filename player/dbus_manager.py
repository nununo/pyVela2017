# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------


from twisted.internet import defer
from twisted import logger

from txdbus import client as txdbus_client



class OMXPlayerDBusManager(object):

    def __init__(self, reactor):

        self.reactor = reactor
        self.log = logger.Logger(namespace='player.dbus')

        self._dbus_conn = None
        self._players_starting = {}
        self._players_stopping = {}


    @property
    def dbus_conn(self):

        if self._dbus_conn is None:
            raise RuntimeError('Not connected to DBus.')
        return self._dbus_conn


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


# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------
