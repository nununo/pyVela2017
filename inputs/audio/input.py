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



_log = logger.Logger(namespace='inputs.audio')



class AudioInput(input_base.InputBase):

    """
    Audio input.
    """
    # TODO: Improve docstring

    def __init__(self, reactor, event_manager, nice_bin, arecord_bin,
                 device, channels, format, rate, buffer_time, respawn_delay):

        super(AudioInput, self).__init__(reactor, event_manager)


    @defer.inlineCallbacks
    def start(self):

        _log.info('started')
        yield defer.succeed(None)


    @defer.inlineCallbacks
    def stop(self):

        _log.info('stopped')
        yield defer.succeed(None)


# ----------------------------------------------------------------------------
# inputs/audio/input.py
# ----------------------------------------------------------------------------
