# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# common/process.py
# ----------------------------------------------------------------------------

"""
Asynchronous, Twisted Based, process management.
"""

from twisted.internet import defer, protocol, error
from twisted import logger



class _TrackProcessProtocol(protocol.ProcessProtocol):

    """
    Twisted ProcessProtocol used to track process startup, exit and output.

    Exposes two relevant attributes:
    - `started`: deferred that fires with PID when the process is started.
    - `stopped`: deferred that fires with exit code when the process terminates.

    If set, calls `out_callable` with process stdout data.
    If set, calls `err_callable` with process stderr data.
    """

    def __init__(self, name, out_callable=None, err_callable=None):

        self._log = logger.Logger(namespace=name)
        self.started = defer.Deferred()
        self.stopped = defer.Deferred()
        self._out_callable = out_callable
        self._err_callable = err_callable
        self._pid = None


    def connectionMade(self):

        # Called by Twisted when the process is started.

        self._pid = self.transport.pid
        self._log.info('process started, PID {p}', p=self._pid)
        self.started.callback(self._pid)


    def outReceived(self, data):

        # Called by Twisted when the process writes to its standard output.

        self._log.debug('stdout: {d!r}', d=data)
        if self._out_callable:
            self._out_callable(data)


    def errReceived(self, data):

        # Called by Twisted when the process writes to its standard error.

        self._log.debug('stderr: {d!r}', d=data)
        if self._err_callable:
            self._err_callable(data)


    def terminate(self):
        """
        Sends a SIGTERM to the process.

        May raise an OSError.
        """
        try:
            self._log.debug('sending SIGTERM')
            self.transport.signalProcess('TERM')
            self._log.debug('sent SIGTERM')
        except error.ProcessExitedAlready:
            self._log.debug('already exited')


    def processEnded(self, reason):

        # Called by Twisted when the process terminates.

        exit_code = reason.value.exitCode
        self._log.info('process ended, exit code {ec}', ec=exit_code)
        self.stopped.callback(exit_code)



def spawn(reactor, cmd_args, name, out_callable=None, err_callable=None):

    """
    Simple wrapper around Twisted's IReactorProcess.spawnProcess.

    Assumes the executable is the first entry in `cmd_args` and ensures
    the current process environment is passed down to the spawned process;
    if `out_callable` / `err_callable` are set, they will be called with
    the spawned process stdout / stderr outputs.

    Returns the associated process protocol instance.
    """

    process_proto = _TrackProcessProtocol(
        name,
        out_callable=out_callable,
        err_callable=err_callable,
    )
    executable = cmd_args[0]

    # env=None, below, is relevant: it ensures that environment variables
    # this process has set are passed down to the child process; in this
    # case, PlayerManager probably set LD_LIBRARY_PATH, and DBusManager
    # probably set DBUS_SESSION_BUS_ADDRESS.

    _process_transport = reactor.spawnProcess(
        process_proto,
        executable,
        cmd_args,
        env=None,
    )
    return process_proto


# ----------------------------------------------------------------------------
# common/process.py
# ----------------------------------------------------------------------------
