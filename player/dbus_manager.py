# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------

"""
Asyncrounous, Twisted Based, DBus connection setup and name tracking.
"""

import os

from twisted.internet import defer
from twisted import logger

from txdbus import client as txdbus_client

from . import process



class DBusManager(object):

    """
    Manages a private DBus instance by spawning a child DBus daemon,
    connecting to it and tracking object names showing up/going away.
    """

    def __init__(self, reactor, settings):

        self.reactor = reactor
        self.log = logger.Logger(namespace='player.dbus')

        # Will be set once the private DBus process is spawned.
        self._dbus_daemon_bin = settings['environment']['dbus_daemon_bin']
        self._dbus_proto = None

        # Our connection to DBus.
        self._dbus_conn = None

        # Will be called on DBus disconnect.
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
        if not self._dbus_proto:
            yield self._spawn_dbus_daemon()

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


    @defer.inlineCallbacks
    def _spawn_dbus_daemon(self):

        # Spawns a child DBus daemon, reads its address from its stdout and
        # sets the DBUS_SESSION_BUS_ADDRESS environment variable (so that we
        # and our child processes can connect to it).

        self.log.info('spawning dbus daemon {ddb!r}', ddb=self._dbus_daemon_bin)
        self._dbus_proto = process.spawn(
            self.reactor,
            [self._dbus_daemon_bin, '--session', '--print-address', '--nofork'],
            'dbus-daemon',
            track_output=True,
        )
        self.log.debug('waiting for dbus daemon start')
        yield self._dbus_proto.started
        self.log.debug('dbus daemon started')

        # Get the first line of output, containing the bus address.
        output_data = None
        try:
            output_deferred = self._dbus_proto.out_queue.get()
            output_deferred.addTimeout(5, self.reactor)
            output_data = yield output_deferred
            output_text = output_data.decode('utf-8')
            output_lines = output_text.split('\n')
            bus_address = output_lines[0]
        except Exception as e:
            self.log.error('bad dbus daemon output {o!r}: {e!r}', o=output_data, e=e)
            raise
        else:
            os.environ['DBUS_SESSION_BUS_ADDRESS'] = bus_address


    @defer.inlineCallbacks
    def cleanup(self):
        """
        Ensures the spawned DBus daemon is properly stopped.
        """
        self.log.info('cleaning up')

        if not self._dbus_proto:
            self.log.info('nothing to cleanup')
            return

        self.log.info('signalling dbus daemon termination')
        try:
            self._dbus_proto.terminate()
        except OSError as e:
            self.log.warn('signalling dbus daemon failed: {e!r}', e=e)
            raise
        else:
            self.log.info('signalled dbus daemon termination')

        self.log.debug('waiting for dbus daemon termination')
        yield self._dbus_proto.stopped
        self.log.debug('dbus daemon terminated')

        self.log.info('cleaned up')


    def _dbus_disconnected(self, _dbus_conn, failure):

        # Called by txdbus when DBus is disconnected.

        self.log.info('lost connection: {f}', f=failure.value)
        self._dbus_conn = None

        # Assume any names being waited on for stopping are gone.
        for name in self._names_stopping:
            self.log.debug('assuming name {n!r} stopped', n=name)
            self._signal_name_change(self._names_stopping, name)
            self.log.debug('assumed name {n!r} stopped', n=name)

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

        self._signal_name_change(tracking_dict, name)


    def _signal_name_change(self, tracking_dict, name):

        # Fires the associated `name` deferred in `tracking_dict`.

        d = tracking_dict.get(name)
        if not d:
            self.log.debug('no deferred for {n!r}', n=name)
            return

        try:
            d.callback(None)
        except defer.AlreadyCalledError:
            self.log.error('failed firing {n!r} deferred', n=name)


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
