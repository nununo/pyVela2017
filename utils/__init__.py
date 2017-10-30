
import sys

from twisted.logger import (globalLogBeginner, textFileLogObserver,
    LogLevelFilterPredicate, FilteringLogObserver, LogLevel)


def setup_logging(debug=False):

    observer = textFileLogObserver(sys.stderr, timeFormat='%H:%M:%S.%f')
    loglevel = LogLevel.debug if debug else LogLevel.info
    predicate = LogLevelFilterPredicate(defaultLogLevel=loglevel)
    predicate.setLogLevelForNamespace(
        'txdbus.client.DBusClientFactory',
        LogLevel.warn,
    )
    observers = [FilteringLogObserver(observer, [predicate])]
    globalLogBeginner.beginLoggingTo(observers)

