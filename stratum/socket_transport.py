from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor, defer

import custom_exceptions
from protocol import Protocol, ClientProtocol
from event_handler import GenericEventHandler

import logger
log = logger.get_logger('socket_transport')

class SocketTransportFactory(ServerFactory):
    def __init__(self, debug=False, signing_key=None, signing_id=None, event_handler=GenericEventHandler):
        self.debug = debug
        self.signing_key = signing_key
        self.signing_id = signing_id
        self.event_handler = event_handler
        self.protocol = Protocol
        
class SocketTransportClientFactory(ReconnectingClientFactory):
    def __init__(self, host, port, allow_trusted=True, allow_untrusted=False,
                 debug=False, signing_key=None, signing_id=None,
                 is_reconnecting=True,
                 event_handler=GenericEventHandler):
        self.debug = debug
        self.is_reconnecting = is_reconnecting
        self.signing_key = signing_key
        self.signing_id = signing_id
        self.client = None # Reference to open connection
        self.on_disconnect = defer.Deferred()
        self.on_connect = defer.Deferred()
        self.peers_trusted = {}
        self.peers_untrusted = {}
        self.main_host = (host, port)
        
        self.event_handler = event_handler
        self.protocol = ClientProtocol
        self.after_connect = []
                    
        self.timeout_handler = reactor.callLater(30, self.connection_timeout)
        reactor.connectTCP(host, port, self)

    '''
    This shouldn't be a part of transport layer
    def add_peers(self, peers):
        # FIXME: Use this list when current connection fails
        for peer in peers:
            hash = "%s%s%s" % (peer['hostname'], peer['ipv4'], peer['ipv6'])
            
            which = self.peers_trusted if peer['trusted'] else self.peers_untrusted
            which[hash] = peer
                 
        #print self.peers_trusted
        #print self.peers_untrusted
    '''
         
    def connection_timeout(self):
        self.timeout_handler = None
        
        if self.client:
            return
        
        e = custom_exceptions.TransportException("SocketTransportClientFactory connection timed out")
        if not self.on_connect.called:
            d = self.on_connect
            self.on_connect = defer.Deferred()
            d.errback(e)
            
        else:
            raise e
        
    def rpc(self, method, params, *args, **kwargs):
        if not self.client:
            raise custom_exceptions.TransportException("Not connected")
        
        return self.client.rpc(method, params, *args, **kwargs)
    
    def subscribe(self, method, params, *args, **kwargs):
        '''
        This is like standard RPC call, except that parameters are stored
        into after_connect list, so the same command will perform again
        on restored connection.
        '''
        if not self.client:
            raise custom_exceptions.TransportException("Not connected")
        
        self.after_connect.append((method, params))
        return self.client.rpc(method, params, *args, **kwargs)
    
    def buildProtocol(self, addr):
        self.resetDelay()
        return ReconnectingClientFactory.buildProtocol(self, addr)
                
    def clientConnectionLost(self, connector, reason):
        if self.is_reconnecting:
            log.debug(reason)
            ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        if self.is_reconnecting:
            log.debug(reason)
            ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)        
        
