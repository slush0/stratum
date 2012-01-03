from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

from protocol import Protocol, ClientProtocol

class SocketTransportFactory(ServerFactory):
    def __init__(self, debug=False, signing_key=None):
        self.debug = debug
        self.signing_key = signing_key
        self.protocol = Protocol
        
class SocketTransportClientFactory(ReconnectingClientFactory):
    protocol = ClientProtocol

    def __init__(self, host, port, debug=False, signing_key=None, on_connect=None):
        self.debug = debug
        self.signing_key = signing_key
        self.client = None # Reference to open connection
        self.on_connect = on_connect
        #reactor.callLater(10, self.connection_timeout)
        reactor.connectTCP(host, port, self)

    '''
    def connection_timeout(self):
        if self.client:
            return
        
        e = Exception("SocketTransportClientFactory connection timed out")
        if self.on_connect:
            self.on_connect.errback(e)
        else:
            raise e
    '''
        
    def rpc(self, *args, **kwargs):
        if not self.client:
            raise Exception("Not connected")
        
        return self.client.rpc(*args, **kwargs)

    def rpc_multi(self, *args, **kwargs):
        if not self.client:
            raise Exception("Not connected")
        
        return self.client.rpc_multi(*args, **kwargs)

    def buildProtocol(self, addr):
        self.resetDelay()
        return ReconnectingClientFactory.buildProtocol(self, addr)
        
    def clientConnectionLost(self, connector, reason):
        #print 'Connection to server lost', reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        #print 'Connection failed. Reason:', reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)        
        
