from twisted.internet.protocol import ServerFactory
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

from protocol import Protocol, ClientProtocol

class SocketTransportFactory(ServerFactory):
    def __init__(self):
        self.protocol = Protocol
        self.client_counter = 0
        
class SocketTransportClientFactory(ReconnectingClientFactory):
    protocol = ClientProtocol

    def __init__(self, host, port, on_connect=None):
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

        '''        
        d = defer.Deferred()
        #d.addErrback(self.error)
        self.request_queue.append((method, list(params), d))
        self.queue_len += 1

        self.process_request()
        return d
        '''

    def buildProtocol(self, addr):
        self.resetDelay()
        return ReconnectingClientFactory.buildProtocol(self, addr)
        #return ClientProtocol()
        
    def clientConnectionLost(self, connector, reason):
        #print 'Connection to server lost', reason
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        #print 'Connection failed. Reason:', reason
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)        
        