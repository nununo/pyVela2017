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

from common import process



_log = logger.Logger(namespace='player.dbus')



class DBusManager(object):

    """
    Manages a private DBus instance by spawning a child DBus daemon,
    connecting to it and tracking object names showing up/going away.
    """

    def __init__(self, reactor, settings):

        self._reactor = reactor

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

        _log.info('connecting to dbus')
        self._dbus_conn = yield txdbus_client.connect(self._reactor, bus_address)
        _log.info('connected to dbus')

        # Track DBus disconnections.
        self._dbus_conn.notifyOnDisconnect(self._dbus_disconnected)
        self._disconnect_callable = disconnect_callable
        _log.debug('tracking disconnections')

        # Use this to track DBus attachments.
        _log.debug('getting org.freedesktop.DBus')
        dbus_obj = yield self.dbus_conn.getRemoteObject(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus'
        )
        _log.debug('subscribing to NameOwnerChanged signal')
        yield dbus_obj.notifyOnSignal(
            'NameOwnerChanged',
            self._dbus_signal_name_owner_changed
        )
        _log.debug('subscribed to NameOwnerChanged signal')


    @defer.inlineCallbacks
    def _spawn_dbus_daemon(self):

        # Spawns a child DBus daemon, reads its address from its stdout and
        # sets the DBUS_SESSION_BUS_ADDRESS environment variable (so that we
        # and our child processes can connect to it).

        stdout_queue = defer.DeferredQueue()

        _log.info('spawning dbus daemon {ddb!r}', ddb=self._dbus_daemon_bin)
        self._dbus_proto = process.spawn(
            self._reactor,
            [self._dbus_daemon_bin, '--session', '--print-address', '--nofork'],
            'player.proc.dbus-daemon',
            out_callable=stdout_queue.put,
        )
        _log.debug('waiting for dbus daemon start')
        yield self._dbus_proto.started
        _log.debug('dbus daemon started')

        # Get the first line of output, containing the bus address.
        output_data = None
        try:
            output_deferred = stdout_queue.get()
            output_deferred.addTimeout(5, self._reactor)
            output_data = yield output_deferred
            output_text = output_data.decode('utf-8')
            output_lines = output_text.split('\n')
            bus_address = output_lines[0]
        except Exception as e:
            _log.error('bad dbus daemon output {o!r}: {e!r}', o=output_data, e=e)
            raise
        else:
            os.environ['DBUS_SESSION_BUS_ADDRESS'] = bus_address


    @defer.inlineCallbacks
    def cleanup(self):
        """
        Ensures the spawned DBus daemon is properly stopped.
        """
        _log.info('cleaning up')

        if not self._dbus_proto:
            _log.info('nothing to cleanup')
            return

        _log.info('signalling dbus daemon termination')
        try:
            self._dbus_proto.terminate()
        except OSError as e:
            _log.warn('signalling dbus daemon failed: {e!r}', e=e)
            raise
        else:
            _log.info('signalled dbus daemon termination')

        _log.debug('waiting for dbus daemon termination')
        yield self._dbus_proto.stopped
        _log.debug('dbus daemon terminated')

        _log.info('cleaned up')


    def _dbus_disconnected(self, _dbus_conn, failure):

        # Called by txdbus when DBus is disconnected.

        _log.info('lost connection: {f}', f=failure.value)
        self._dbus_conn = None

        # Assume any names being waited on for stopping are gone.
        for name in self._names_stopping:
            _log.debug('assuming name {n!r} stopped', n=name)
            self._signal_name_change(self._names_stopping, name)
            _log.debug('assumed name {n!r} stopped', n=name)

        if self._disconnect_callable:
            try:
                self._disconnect_callable()
            except Exception as e:
                _log.warn('disconnect callable failed: {e}', e=e)


    def _dbus_signal_name_owner_changed(self, name, old_addr, new_addr):

        # DBus NameOwnerChanged signal handler
        # ------------------------------------
        # `old_addr` will be '' if name just showed up on the bus.
        # `new_addr` will be '' if name is just gone from the bus.

        _log.debug('name {n!r} owner change: {f!r} to {t!r}', n=name,
                   f=old_addr, t=new_addr)
        if not old_addr:
            tracking_dict = self._names_starting
        elif not new_addr:
            tracking_dict = self._names_stopping
        else:
            _log.error('unexpected signal data')

        self._signal_name_change(tracking_dict, name)


    @staticmethod
    def _signal_name_change(tracking_dict, name):

        # Fires the associated `name` deferred in `tracking_dict`.

        d = tracking_dict.get(name)
        if not d:
            _log.debug('no deferred for {n!r}', n=name)
            return

        try:
            if not d.called:
                d.callback(None)
        except Exception as e:
            _log.error('failed firing {n!r} deferred: {e!r}', n=name, e=e)


    def track_dbus_name(self, name):
        """
        Starts `name` lifecycle tracking on DBus.
        """
        if name in self._names_starting:
            raise RuntimeError('Name %r already tracked.' % (name, ))

        # These will fire, respectively, when name shows up/goes away.
        self._names_starting[name] = defer.Deferred()
        self._names_stopping[name] = defer.Deferred()
        _log.info('tracking dbus name {n!r}', n=name)


    @defer.inlineCallbacks
    def wait_dbus_name_start(self, name):
        """
        Returns a deferred that fires when `name` shows up on the bus.
        """
        try:
            _log.info('waiting name {n!r} start', n=name)
            yield self._names_starting[name]
            _log.info('name {n!r} started', n=name)
            del self._names_starting[name]
        except KeyError:
            raise RuntimeError('name %r not tracked.' % (name,))


    @defer.inlineCallbacks
    def wait_dbus_name_stop(self, name):
        """
        Returns a deferred that fires when `name` goes away from the bus.
        """
        try:
            _log.info('waiting name {n!r} stop', n=name)
            yield self._names_stopping[name]
            _log.info('name {n!r} stopped', n=name)
            del self._names_stopping[name]
        except KeyError:
            raise RuntimeError('name %r not tracked.' % (name,))


# ----------------------------------------------------------------------------
# player/dbus_manager.py
# ----------------------------------------------------------------------------
