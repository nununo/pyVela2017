# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------

"""
Asyncrounous, Twisted Based, DBus connection setup and name tracking.
"""

from twisted.internet import defer
from twisted import logger

from txdbus import client as txdbus_client



class DBusManager(object):

    """
    Connects to DBus and tracks object names showing up/going away.
    """

    def __init__(self, reactor):

        self.reactor = reactor
        self.log = logger.Logger(namespace='player.dbus')

        self._dbus_conn = None

        # Will be called on disconnect.
        self._disconnect_callable = None

        # keys/values: DBus names/Twisted deferreds
        self._names_starting = {}
        self._names_stopping = {}


    @property
    def dbus_conn(self):
        """
        DBus connection object.
        Only available after a successful call to `connect_to_dbus`.
        """
        if self._dbus_conn is None:
            raise RuntimeError('Not connected to DBus.')
        return self._dbus_conn


    @defer.inlineCallbacks
    def connect_to_dbus(self, bus_address='session', disconnect_callable=None):
        """
        Connects to DBus and sets up DBus object name tracking.
        """
        self.log.info('connecting to dbus')
        self._dbus_conn = yield txdbus_client.connect(self.reactor, bus_address)
        self.log.info('connected to dbus')

        # Track DBus disconnections.
        self._dbus_conn.notifyOnDisconnect(self._dbus_disconnected)
        self._disconnect_callable = disconnect_callable
        self.log.debug('tracking disconnections')

        # Use this to track DBus attachments.
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


    def _dbus_disconnected(self, _dbus_conn, failure):

        # Called by txdbus when DBus is disconnected.

        self.log.info('lost connection: {f}', f=failure.value)
        self._dbus_conn = None

        if self._disconnect_callable:
            try:
                self._disconnect_callable()
            except Exception as e:
                self.log.warn('disconnect callable failed: {e}', e=e)


    def _dbus_signal_name_owner_changed(self, name, old_addr, new_addr):

        # DBus NameOwnerChanged signal handler
        # ------------------------------------
        # `old_addr` will be '' if name just showed up on the bus.
        # `new_addr` will be '' if name is just gone from the bus.

        self.log.debug('name {n!r} owner change: {f!r} to {t!r}', n=name,
                       f=old_addr, t=new_addr)
        if not old_addr:
            tracking_dict = self._names_starting
        elif not new_addr:
            tracking_dict = self._names_stopping
        else:
            self.log.error('unexpected signal data')

        d = tracking_dict.get(name)
        if d:
            # `name` is being tracked: fire the deferred.
            d.callback(name)


    def track_dbus_name(self, name):
        """
        Starts `name` lifecycle tracking on DBus.
        """
        if name in self._names_starting:
            raise RuntimeError('Name %r already tracked.' % (name, ))

        # These will fire, respectively, when name shows up/goes away.
        self._names_starting[name] = defer.Deferred()
        self._names_stopping[name] = defer.Deferred()
        self.log.info('tracking dbus name {n!r}', n=name)


    @defer.inlineCallbacks
    def wait_dbus_name_start(self, name):
        """
        Returns a deferred that fires when `name` shows up on the bus.
        """
        try:
            self.log.info('waiting name {n!r} start', n=name)
            yield self._names_starting[name]
            self.log.info('name {n!r} started', n=name)
            del self._names_starting[name]
        except KeyError:
            raise RuntimeError('name %r not tracked.' % (name,))


    @defer.inlineCallbacks
    def wait_dbus_name_stop(self, name):
        """
        Returns a deferred that fires when `name` goes away from the bus.
        """
        try:
            self.log.info('waiting name {n!r} stop', n=name)
            yield self._names_stopping[name]
            self.log.info('name {n!r} stopped', n=name)
            del self._names_stopping[name]
        except KeyError:
            raise RuntimeError('name %r not tracked.' % (name,))


# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------
