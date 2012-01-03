from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory

from halfnode import BitcoinP2PProtocol

'''
This is simple wrapper around generic Halfnode implementation.
It keep one open P2P connection to trusted Bitcoin node.
'''

# Instance of BitcoinP2PProtocol connected to trusted Bitcoin node
_connection = None

def get_connection():
    if not _connection:
        raise Exception("Trusted node not connected")
    return _connection

class P2PProtocol(BitcoinP2PProtocol):
    def connectionMade(self):
        BitcoinP2PProtocol.connectionMade(self)
        print "P2P connected"

        global _connection
        _connection = self

    def connectionLost(self, reason):
        BitcoinP2PProtocol.connectionLost(self, reason)
        print "P2P disconnected"

        global _connection
        _connection = None

class P2PFactory(ReconnectingClientFactory):
    def startFactory(self):
        ReconnectingClientFactory.startFactory(self)

    def buildProtocol(self, addr):
        self.resetDelay()
        return P2PProtocol()

def run(host):
    print host
    reactor.connectTCP(host, 8333, P2PFactory())
