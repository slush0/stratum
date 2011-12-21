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

import socket_transport
import httppoll_transport

import settings

def setup_services():

    #dbpool = adbapi.ConnectionPool(settings.DATABASE_DRIVER, host=settings.DATABASE_HOST, user=settings.DATABASE_USER,
    #                               passwd=settings.DATABASE_PASSWORD, db=settings.DATABASE_DBNAME, cp_reconnect=True)

    import server_repository
	
    # Set up thread pool size for service threads
    reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE) 
    
    # Attach Socket Transport service to application
    socket = internet.TCPServer(settings.LISTEN_SOCKET_TRANSPORT, socket_transport.SocketTransportFactory(debug=settings.DEBUG))
    socket.setServiceParent(application)

    # Attach HTTP Poll Transport service to application
    httppoll = internet.TCPServer(settings.LISTEN_HTTPPOLL_TRANSPORT, Site(httppoll_transport.Root(debug=settings.DEBUG)))
    httppoll.setServiceParent(application)

    # Attach HTTPS Poll Transport service to application
    sslContext = ssl.DefaultOpenSSLContextFactory(settings.SSL_PRIVKEY, settings.SSL_CACERT)
    httpspoll = internet.SSLServer(settings.LISTEN_HTTPSPOLL_TRANSPORT, Site(httppoll_transport.Root(debug=settings.DEBUG)),
                                   contextFactory = sslContext)
    httpspoll.setServiceParent(application)

    '''
    wsgiThreadPool = ThreadPool()
    wsgiThreadPool.start()
    reactor.addSystemEventTrigger('after', 'shutdown', wsgiThreadPool.stop)
    	

    wsgi = WSGIResource(reactor, wsgiThreadPool, application)
    wsgipoll = internet.TCPServer(settings.LISTEN_WSGIPOLL_TRANSPORT, Site(wsgi))
    wsgipoll.setServiceParent(application)
    '''
	
def heartbeat():
    print 'heartbeat'
    reactor.callLater(60, heartbeat)

if settings.DEBUG:
    reactor.callLater(0, heartbeat)

application = service.Application("electrum-server")
setup_services()
