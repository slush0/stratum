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
#from twisted.python.logfile import DailyLogFile
import OpenSSL.SSL

import socket_transport
import http_transport
import websocket_transport
import irc

try:
    import settings
except ImportError:
    print "***** Is settings.py missing? Maybe you want to copy and customize settings.sample.py?"

def setup_services():

    #dbpool = adbapi.ConnectionPool(settings.DATABASE_DRIVER, host=settings.DATABASE_HOST, user=settings.DATABASE_USER,
    #                               passwd=settings.DATABASE_PASSWORD, db=settings.DATABASE_DBNAME, cp_reconnect=True)
        
    try:
        import signature
        signing_key = signature.load_privkey_pem(settings.SIGNING_KEY)
    except:
        print "Loading of signing key '%s' failed, protocol messages cannot be signed." % settings.SIGNING_KEY
        signing_key = None
        
    # Attach HTTPS Poll Transport service to application
    try:
        sslContext = ssl.DefaultOpenSSLContextFactory(settings.SSL_PRIVKEY, settings.SSL_CACERT)
    except OpenSSL.SSL.Error:
        sslContext = None
        print "Cannot initiate SSL context, are SSL_PRIVKEY or SSL_CACERT missing?"
        print "This will skip all SSL-based transports."
        
    # Load all services from service_repository module.
    try:
        import service_repository
    except ImportError:
        print "***** Is service_repository missing? Add service_repository module to your python path!"
	
    if settings.ENABLE_EXAMPLE_SERVICE:
        import example_service
        
    # Set up thread pool size for service threads
    reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE) 
    
    if settings.LISTEN_SOCKET_TRANSPORT:
        # Attach Socket Transport service to application
        socket = internet.TCPServer(settings.LISTEN_SOCKET_TRANSPORT,
                                socket_transport.SocketTransportFactory(debug=settings.DEBUG,
                                                                        signing_key=signing_key,
                                                                        signing_id=settings.SIGNING_ID))
        socket.setServiceParent(application)

    # Build the HTTP interface
    httpsite = Site(http_transport.Root(debug=settings.DEBUG, signing_key=signing_key, signing_id=settings.SIGNING_ID))
    httpsite.sessionFactory = http_transport.HttpSession

    if settings.LISTEN_HTTP_TRANSPORT:    
        # Attach HTTP Poll Transport service to application
        http = internet.TCPServer(settings.LISTEN_HTTP_TRANSPORT, httpsite)
        http.setServiceParent(application)

    if settings.LISTEN_HTTPS_TRANSPORT and sslContext:
            https = internet.SSLServer(settings.LISTEN_HTTPS_TRANSPORT, httpsite, contextFactory = sslContext)
            https.setServiceParent(application)
    
    if settings.LISTEN_WS_TRANSPORT:
        from autobahn.websocket import listenWS
        log.msg("Starting WS transport on %d" % settings.LISTEN_WS_TRANSPORT)
        ws = websocket_transport.WebsocketTransportFactory(settings.LISTEN_WS_TRANSPORT)
        listenWS(ws)
    
    if settings.LISTEN_WSS_TRANSPORT and sslContext:  
        from autobahn.websocket import listenWS
        log.msg("Starting WSS transport on %d" % settings.LISTEN_WSS_TRANSPORT)
        wss = websocket_transport.WebsocketTransportFactory(settings.LISTEN_WSS_TRANSPORT, is_secure=True)
        listenWS(wss, contextFactory=sslContext)
    
    if settings.IRC_NICK:
        reactor.connectTCP(settings.IRC_SERVER, settings.IRC_PORT, irc.IrcLurkerFactory(settings.IRC_ROOM, settings.IRC_NICK, settings.IRC_HOSTNAME))
    
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

application = service.Application("stratum-server")
setup_services()
