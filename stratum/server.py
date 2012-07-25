def setup():
    try:
        from twisted.internet import epollreactor
        epollreactor.install()
    except ImportError:
        print "Failed to install epoll reactor!"
    
    from twisted.application import service, internet
    from twisted.internet import reactor, ssl
    from twisted.web.server import Site
    from twisted.python import log
    #from twisted.enterprise import adbapi
    #from twisted.web.wsgi import WSGIResource
    import OpenSSL.SSL
    
    try:
        import settings
    except ImportError:
        print "***** Is configs.py missing? Maybe you want to copy and customize config_default.py?"

    if settings.ENABLE_EXAMPLE_SERVICE:
        import stratum.example_service

    import socket_transport
    import http_transport
    import websocket_transport
    import irc
    
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
        
    # Set up thread pool size for service threads
    reactor.suggestThreadPoolSize(settings.THREAD_POOL_SIZE) 
    
    application = service.Application("stratum-server")
    
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
        ws = websocket_transport.WebsocketTransportFactory(settings.LISTEN_WS_TRANSPORT,
                                                           debug=settings.DEBUG,
                                                           signing_key=signing_key,
                                                           signing_id=settings.SIGNING_ID)
        listenWS(ws)
    
    if settings.LISTEN_WSS_TRANSPORT and sslContext:  
        from autobahn.websocket import listenWS
        log.msg("Starting WSS transport on %d" % settings.LISTEN_WSS_TRANSPORT)
        wss = websocket_transport.WebsocketTransportFactory(settings.LISTEN_WSS_TRANSPORT, is_secure=True,
                                                            debug=settings.DEBUG,
                                                            signing_key=signing_key,
                                                            signing_id=settings.SIGNING_ID)
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
        
    return application

if __name__ == '__main__':
    print "This is not executable script. Try 'twistd -ny launcher.tac instead!"