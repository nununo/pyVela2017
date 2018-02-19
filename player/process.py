# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# player/process.py
# ----------------------------------------------------------------------------

"""
Asyncrounous, Twisted Based, process management.
"""

from twisted.internet import defer, protocol, error
from twisted import logger



class _TrackProcessProtocol(protocol.ProcessProtocol):

    """
    Twisted ProcessProtocol used to track process startup, exit and output.

    Exposes two relevant attributes:
    - `started`: deferred that fires with PID when the process is started.
    - `stopped`: deferred that fires with exit code when the process terminates.

    If initialized with `track_output` to True, additionally exposes:
    - `out_queue`: deferred queue that fires with process stdout data.
    - `err_queue`: deferred queue that fires with process stderr data.
    """

    def __init__(self, name, track_output=False):

        self.log = logger.Logger(namespace='player.proc.%s' % (name,))
        self.started = defer.Deferred()
        self.stopped = defer.Deferred()
        self.out_queue = defer.DeferredQueue() if track_output else None
        self.err_queue = defer.DeferredQueue() if track_output else None
        self._track_output = track_output
        self.pid = None


    def connectionMade(self):

        # Called by Twisted when the process is started.

        self.pid = self.transport.pid
        self.log.info('process started, PID {p}', p=self.pid)
        self.started.callback(self.pid)


    def outReceived(self, data):

        # Called by Twisted when the process writes to its standard output.

        self.log.debug('stdout: {d!r}', d=data)
        if self._track_output:
            self.out_queue.put(data)


    def errReceived(self, data):

        # Called by Twisted when the process writes to its standard error.

        self.log.debug('stderr: {d!r}', d=data)
        if self._track_output:
            self.err_queue.put(data)


    def terminate(self):
        """
        Sends a SIGTERM to the process.

        May raise an OSError.
        """
        try:
            self.log.debug('sending SIGTERM')
            self.transport.signalProcess('TERM')
            self.log.debug('sent SIGTERM')
        except error.ProcessExitedAlready:
            self.log.debug('already exited')


    def processEnded(self, reason):

        # Called by Twisted when the process terminates.

        exit_code = reason.value.exitCode
        self.log.info('process ended, exit code {ec}', ec=exit_code)
        self.stopped.callback(exit_code)



def spawn(reactor, cmd_args, name, track_output=False):

    """
    Simple wrapper around Twisted's IReactorProcess.spawnProcess.

    Assumes the executable is the first entry in `cmd_args` and ensures
    the current process environment is passed down to the spawned process;
    when `track_output` is True, the returned protocol instance uses two
    deferred queues that fire with the spawned process stdout and stderr
    data.

    Returns the associated process protocol instance.
    """

    process_proto = _TrackProcessProtocol(name, track_output=track_output)
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
# player/process.py
# ----------------------------------------------------------------------------
