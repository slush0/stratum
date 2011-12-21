from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

from protocol import Protocol, ClientProtocol

class SocketTransportFactory(ServerFactory):
    def __init__(self, debug=False):
        self.debug = debug
        self.protocol = Protocol
        
class SocketTransportClientFactory(ReconnectingClientFactory):
    protocol = ClientProtocol

    def __init__(self, host, port, debug=False, on_connect=None):
        self.debug = debug
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
        
    def rpc(self, method, params, expect_response=True):
        if not self.client:
            raise Exception("Not connected")
        
        return self.client.rpc(method, params, expect_response)

    def rpc_multi(self, methods):
        if not self.client:
            raise Exception("Not connected")
        
        return self.client.rpc_multi(methods)

    def buildProtocol(self, addr):
        self.resetDelay()
        return ReconnectingClientFactory.buildProtocol(self, addr)
        
    def clientConnectionLost(self, connector, reason):
        #print 'Connection to server lost', reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        #print 'Connection failed. Reason:', reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)        
        