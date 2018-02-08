# ----------------------------------------------------------------------------
# vim: ts=4:sw=4:et
# ----------------------------------------------------------------------------
# webserver/http.py
# ----------------------------------------------------------------------------


import os

from twisted.web import server, static
from twisted import logger



_log = logger.Logger(namespace='webserver.http')



def setup_webserver(reactor):

    web_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'web-root'))
    site = server.Site(static.File(web_root))

    reactor.listenTCP(8080, site, interface='0.0.0.0')
    _log.info('listening for HTTP connections on 0.0.0.0:8080')


# ----------------------------------------------------------------------------
# webserver/http.py
# ----------------------------------------------------------------------------
