# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# inputs/audio/input.py
# ----------------------------------------------------------------------------

"""
The audio input.
"""


from twisted.internet import defer
from twisted import logger

from inputs import input_base
from common import process



_log = logger.Logger(namespace='inputs.audio')



class AudioInput(input_base.InputBase):

    """
    Audio input.
    """
    # TODO: Improve docstring

    def __init__(self, reactor, event_manager, nice_bin, arecord_bin,
                 device, channels, format, rate, buffer_time, respawn_delay):

        super(AudioInput, self).__init__(reactor, event_manager)
        self._spawn_args = [
            nice_bin,
            arecord_bin,
            '--device=%s' % (device,),
            '--channels=%s' % (channels,),
            '--format=%s' % (format,),
            '--rate=%s' % (rate,),
            '--buffer-time=%s' % (buffer_time,),
            '-vvv',
            '/dev/null',
        ]
        self._respawn_delay = float(respawn_delay)
        self._arecord_proto = None
        self._output_callable = event_manager.audio


    @defer.inlineCallbacks
    def start(self):

        _log.info('starting')
        yield self._spawn_arecord()
        _log.info('started')


    @defer.inlineCallbacks
    def _spawn_arecord(self):

        _log.debug('spawning arecord')
        self._arecord_proto = process.spawn(
            self._reactor,
            self._spawn_args,
            'inputs.audio.proc',
            err_callable=self._handle_arecord_output,
        )
        _log.debug('waiting arecord start')
        yield self._arecord_proto.started
        _log.debug('arecord started')

        self._arecord_proto.stopped.addCallback(self._arecord_stopped)


    def _arecord_stopped(self, exit_code):

        _log.warn('arecord stopped with exit code {ec!r}', ec=exit_code)
        self._arecord_proto = None

        respawn_delay = self._respawn_delay
        if respawn_delay < 0:
            _log.warn('will not re-spawn arecord')
            return

        _log.warn('re-spawning arecord in {d:.3f} seconds', d=respawn_delay)
        self._reactor.callLater(respawn_delay, self._spawn_arecord)


    def _handle_arecord_output(self, data):

        _log.debug('arecord output data={d!r}', d=data)
        if not data.startswith(b'Max peak'):
            return

        try:
            reading = int(data[data.rfind(b' ')+1:-2])
        except Exception as e:
            _log.warn('bad data {d!r}: {e!r}', d=data, e=e)
        else:
            self._output_callable(reading)


    @defer.inlineCallbacks
    def stop(self):

        _log.info('stopping')

        if not self._arecord_proto:
            _log.info('no arecord process to stop')
            return

        _log.info('signalling arecord termination')
        try:
            self._arecord_proto.terminate()
        except OSError as e:
            _log.warn('signalling arecord failed: {e!r}', e=e)
            raise
        else:
            _log.info('signalled arecord termination')

        _log.debug('waiting for arecord termination')
        yield self._arecord_proto.stopped
        _log.debug('arecord terminated')

        _log.info('stopped')

        yield defer.succeed(None)


# ----------------------------------------------------------------------------
# inputs/audio/input.py
# ----------------------------------------------------------------------------
