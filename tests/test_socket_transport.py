from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet import defer
import time

import sys
sys.path.append('../')

from socket_transport import SocketTransportClientFactory

HOSTNAME='localhost'
PORT=3333

class TcpTransportTestCase(unittest.TestCase):
    
    def _connect(self, hostname, port, on_connect, on_disconnect):
        # Try to connect to remote server        
        return SocketTransportClientFactory(hostname, port,
                allow_trusted=True,
                allow_untrusted=False,
                debug=False,
                signing_key=None,
                signing_id=None,
                on_connect=on_connect,
                on_disconnect=on_disconnect,
                is_reconnecting=False)
        
    @defer.inlineCallbacks
    def setUp(self):
        self.on_connect = defer.Deferred()
        self.on_disconnect = defer.Deferred()       
        self.f = self._connect(HOSTNAME, PORT, self.on_connect, self.on_disconnect)
        yield self.on_connect
     
    @defer.inlineCallbacks
    def tearDown(self):
        self.f.client.transport.loseConnection()
        yield self.on_disconnect
      
    @defer.inlineCallbacks
    def test_connection_timeout(self):
        on_connect = defer.Deferred()
        d = self.failUnlessFailure(on_connect, Exception)
        self._connect(HOSTNAME, 50999, on_connect, None)
                
        print "Please wait, this will take few seconds to complete..."
        yield d

    @defer.inlineCallbacks
    def test_ping(self):
        result = (yield self.f.rpc('node.ping', ['Some data',]))
        self.assertEquals(result, 'Some data', 'hu')
          
    @defer.inlineCallbacks
    def test_banner(self):
        result = (yield self.f.rpc('node.get_banner', []))
        self.assertSubstring('', result)
        
#if __name__ == '__main__':
#    unittest.main()