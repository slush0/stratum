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
from twisted.internet import reactor, defer
from twisted.internet.defer import inlineCallbacks, returnValue

from socket_transport import SocketTransportFactory

import settings_server as settings

def setup_services():

    #dbpool = adbapi.ConnectionPool(settings.DATABASE_DRIVER, host=settings.DATABASE_HOST, user=settings.DATABASE_USER,
    #                               passwd=settings.DATABASE_PASSWORD, db=settings.DATABASE_DBNAME, cp_reconnect=True)

    import server_repository
	
    # Attach Socket Transport service to application
    getwork_service = internet.TCPServer(settings.LISTEN_SOCKET_TRANSPORT, SocketTransportFactory())
    getwork_service.setServiceParent(application)
    
def heartbeat():
    print 'heartbeat'
    reactor.callLater(60, heartbeat)

if settings.DEBUG:
    reactor.callLater(0, heartbeat)

application = service.Application("electrum-server")
setup_services()
