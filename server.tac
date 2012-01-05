# You can run this .tac file directly with:
#    twistd -ny server.tac

try:
    from twisted.internet import epollreactor
    epollreactor.install()
except ImportError:
    print "Failed to install epoll reactor!"

import sys
import os
import base64

from twisted.enterprise import adbapi
from twisted.application import service, internet
from twisted.internet import reactor, defer, ssl
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.python.threadpool import ThreadPool
from twisted.python import log
from twisted.python.logfile import DailyLogFile
import OpenSSL.SSL

import socket_transport
import http_transport

import settings

def setup_services():

    #dbpool = adbapi.ConnectionPool(settings.DATABASE_DRIVER, host=settings.DATABASE_HOST, user=settings.DATABASE_USER,
    #                               passwd=settings.DATABASE_PASSWORD, db=settings.DATABASE_DBNAME, cp_reconnect=True)
        
    try:
        import signature
        signing_key = signature.load_privkey_pem(settings.SIGNING_KEY)
    except:
        print "Loading of signing key '%s' failed, protocol messages cannot be signed." % settings.SIGNING_KEY
        signing_key = None
        
    # Load all services in /service_repository/ directory.
    import server_repository
	
    # Set up thread pool size for service threads
    reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE) 
    
    # Attach Socket Transport service to application
    socket = internet.TCPServer(settings.LISTEN_SOCKET_TRANSPORT,
                                socket_transport.SocketTransportFactory(debug=settings.DEBUG, signing_key=signing_key))
    socket.setServiceParent(application)

    # Build the HTTP interface
    httpsite = Site(http_transport.Root(debug=settings.DEBUG, signing_key=signing_key))
    httpsite.sessionFactory = http_transport.HttpSession
    
    # Attach HTTP Poll Transport service to application
    http = internet.TCPServer(settings.LISTEN_HTTPPOLL_TRANSPORT, httpsite)
    http.setServiceParent(application)

    # Attach HTTPS Poll Transport service to application
    try:
        sslContext = ssl.DefaultOpenSSLContextFactory(settings.SSL_PRIVKEY, settings.SSL_CACERT)
    except OpenSSL.SSL.Error:
        print "Cannot initiate SSL context, are SSL_PRIVKEY or SSL_CACERT missing?"
        print "Skipping HTTPS Poll transport."
    else:
        https = internet.SSLServer(settings.LISTEN_HTTPSPOLL_TRANSPORT, httpsite, contextFactory = sslContext)
        https.setServiceParent(application)
        
    '''
    wsgiThreadPool = ThreadPool()
    wsgiThreadPool.start()
    reactor.addSystemEventTrigger('after', 'shutdown', wsgiThreadPool.stop)
    	

    wsgi = WSGIResource(reactor, wsgiThreadPool, application)
    wsgipoll = internet.TCPServer(settings.LISTEN_WSGIPOLL_TRANSPORT, Site(wsgi))
    wsgipoll.setServiceParent(application)
    '''
	
def heartbeat():
    log.msg('heartbeat')
    reactor.callLater(60, heartbeat)

if settings.DEBUG:
    reactor.callLater(0, heartbeat)

application = service.Application("electrum-server")
setup_services()
