# ----------------------------------------------------------------------------
# log/__init__.py
# ----------------------------------------------------------------------------

"""
Exports two functions to simplify twisted.logger utilization.
"""


import logging
import sys

from twisted.logger import (
    globalLogBeginner, textFileLogObserver,
    FilteringLogObserver, LogLevelFilterPredicate, LogLevel, Logger,
)



class _TwistedLoggerHandler(logging.Handler):

    """
    Standard library logging.Handler that emits log records towards
    twisted.logger, such that:
    - namespace will be logger's name prefixed with 'stdlib.', by default.
    - level matches the emitted record level, falling back to t.l.LogLevel.error
      if no match is found.
    - message is build from the emmited record msg and args attributes.
    """

    _LEVELS = {
        10: LogLevel.debug,
        20: LogLevel.info,
        30: LogLevel.warn,
        40: LogLevel.error,
        50: LogLevel.critical,
    }

    def __init__(self, prefix='stdlib.'):

        super(_TwistedLoggerHandler, self).__init__()
        self._prefix = prefix


    def emit(self, record):

        namespace = '%s%s' % (self._prefix, record.name)
        rounded_level = 10 * (record.levelno // 10)
        log_level = self._LEVELS.get(rounded_level, LogLevel.error)
        try:
            message = record.msg % record.args
        except Exception:
            message = record.msg
        Logger(namespace=namespace).emit(log_level, message)



class _LogManager(object):

    """
    Twisted logger manager: tracks filtering predicates to support dynamic
    per-namespace log level changes at runtime.
    """

    def __init__(self):

        self._predicate = None


    def setup(self, level, namespace_levels, text_file, time_format,
              handle_stdlib, stdlib_level, stdlib_prefix, observer):
        """
        Initiates the twisted.logger system:
        - level: default log level as a string (ie: 'warn', 'info', ....).
        - namespace_levels: a dict of namespaces/log level names.
        - text_file: where to write the log to.
        - time_format: as supported by datetime.strftime.
        - handle_stdlib: True/False.
        - stdlib_level: level name, above which stdlib logging is handled.
        - stdlib_prefix: added to stdlib logger name, used as namespace.
        - observer: additional observer.
        """
        base_observer = textFileLogObserver(text_file, timeFormat=time_format)
        self._predicate = LogLevelFilterPredicate(
            defaultLogLevel=LogLevel.levelWithName(level),
        )
        if namespace_levels:
            for namespace, level_name in namespace_levels.items():
                level = LogLevel.levelWithName(level_name)
                self._predicate.setLogLevelForNamespace(namespace, level)
        filtered_observer = FilteringLogObserver(base_observer, [self._predicate])
        xx = FilteringLogObserver(observer, [self._predicate])
        globalLogBeginner.beginLoggingTo([filtered_observer, xx])

        if handle_stdlib:
            self._handle_stdlib(stdlib_level, stdlib_prefix)


    @staticmethod
    def _handle_stdlib(level_name, prefix):
        """
        Directs standard library logging records to twisted.logger.
        Standard library log recods will be handled at `level_name` or
        above and logged to a namespace prefixed by `prefix`.
        """
        stdlib_root_logger = logging.getLogger()
        try:
            level = getattr(logging, level_name.upper())
        except AttributeError:
            raise ValueError(level_name)
        stdlib_root_logger.setLevel(level)
        handler = _TwistedLoggerHandler(prefix)
        stdlib_root_logger.addHandler(handler)


    def set_level(self, namespace=None, level_name=None):
        """
        Change the logging level of namespace to level.
        If namespace is None, sets all namespaces to level_name.
        If level_name is None, uses the default log level.
        """
        if level_name:
            level = LogLevel.levelWithName(level_name)
        else:
            level = self._predicate.defaultLogLevel
        if namespace:
            self._predicate.setLogLevelForNamespace(namespace, level)
        else:
            self._predicate.defaultLogLevel = level
            self._predicate.clearLogLevels()



_LOG_MGR = _LogManager()


def setup(level='warn', namespace_levels=None, text_file=sys.stderr,
          time_format='%H:%M:%S.%f', handle_stdlib=True,
          stdlib_level='notset', stdlib_prefix='stdlib.',
          observer=None):
    """
    Initializes the twisted.logger system.
    """
    _LOG_MGR.setup(
        level, namespace_levels, text_file, time_format,
        handle_stdlib, stdlib_level, stdlib_prefix, observer,
    )


def set_level(namespace=None, level=None):
    """
    Change the log level of namespace.
    """
    _LOG_MGR.set_level(namespace, level)


# ----------------------------------------------------------------------------
# log/__init__.py
# ----------------------------------------------------------------------------
