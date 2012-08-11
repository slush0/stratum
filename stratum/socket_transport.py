from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

from protocol import Protocol, ClientProtocol
from event_handler import GenericEventHandler

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
                 on_connect=None, on_disconnect=None, is_reconnecting=True,
                 event_handler=GenericEventHandler):
        self.debug = debug
        self.is_reconnecting = is_reconnecting
        self.signing_key = signing_key
        self.signing_id = signing_id
        self.client = None # Reference to open connection
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.peers_trusted = {}
        self.peers_untrusted = {}
        self.main_host = (host, port)
        
        self.event_handler = event_handler
        self.protocol = ClientProtocol

        self.timeout_handler = reactor.callLater(10, self.connection_timeout)
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
        
        e = Exception("SocketTransportClientFactory connection timed out")
        if self.on_connect:
            self.on_connect.errback(e)
        else:
            raise e
        
    def rpc(self, *args, **kwargs):
        if not self.client:
            raise Exception("Not connected")
        
        return self.client.rpc(*args, **kwargs)
    
    def buildProtocol(self, addr):
        self.resetDelay()
        return ReconnectingClientFactory.buildProtocol(self, addr)
        
    def clientConnectionLost(self, connector, reason):
        #print 'Connection to server lost', reason
        if self.is_reconnecting:
            ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        #print 'Connection failed. Reason:', reason
        if self.is_reconnecting:
            ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)        
        
