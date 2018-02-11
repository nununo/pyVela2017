# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# webserver/http.py
# ----------------------------------------------------------------------------


"""
An asyncronous, Twisted based, minimal HTTP server.
"""

import os

from twisted.web import server, static
from twisted import logger



_log = logger.Logger(namespace='webserver.http')



def setup_webserver(reactor):

    """
    Starts listening for HTTP requests, serving static files from a directory
    named 'web-root' in this module's directory.

    Serves .gz ending files when asked for the compressed URLs.
    """

    web_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'web-root'))
    site = server.Site(static.File(web_root, ignoredExts=('.gz',)))

    # TODO: Should port/interface be configurable?
    reactor.listenTCP(8080, site, interface='0.0.0.0')
    _log.info('listening for HTTP connections on 0.0.0.0:8080')


# ----------------------------------------------------------------------------
# webserver/http.py
# ----------------------------------------------------------------------------
