# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------


from twisted.internet import defer
from twisted import logger

from txdbus import client as txdbus_client



class DBusManager(object):

    def __init__(self, reactor):

        self.reactor = reactor
        self.log = logger.Logger(namespace='player.dbus')

        self._dbus_conn = None
        self._names_starting = {}
        self._names_stopping = {}


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


    def _dbus_signal_name_owner_changed(self, name, old_addr, new_addr):

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
            d.callback(name)


    def track_dbus_name(self, name):

        if name in self._names_starting:
            raise RuntimeError('Name %r already tracked.' % (name, ))

        self._names_starting[name] = defer.Deferred()
        self._names_stopping[name] = defer.Deferred()
        self.log.info('tracking dbus name {n!r}', n=name)


    @defer.inlineCallbacks
    def wait_dbus_name_start(self, name):

        try:
            self.log.info('waiting name {n!r} start', n=name)
            yield self._names_starting[name]
            self.log.info('name {n!r} started', n=name)
            del self._names_starting[name]
        except KeyError:
            raise RuntimeError('name %r not tracked.' % (name,))


    @defer.inlineCallbacks
    def wait_dbus_name_stop(self, name):

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
