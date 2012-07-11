from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
import StringIO
import binascii

import logger
log = logger.get_logger('p2pnode')

try:
    # Provide deserialization for Bitcoin transactions
    import Abe.deserialize
    is_Abe = True
except ImportError:
    print "Abe not installed, some extended features won't be available"
    is_Abe = False

import halfnode

'''
This is wrapper around generic Halfnode implementation.

Features:
  * Keep one open P2P connection to trusted Bitcoin node
  * Provide broadcast_tx method for broadcasting new transactions
'''

# Instance of BitcoinP2PProtocol connected to trusted Bitcoin node
_connection = None

def get_connection():
    if not _connection:
        raise Exception("Trusted node not connected")
    return _connection

class P2PProtocol(halfnode.BitcoinP2PProtocol):
    def connectionMade(self):
        halfnode.BitcoinP2PProtocol.connectionMade(self)
        log.info("P2P connected")

        global _connection
        _connection = self

    def connectionLost(self, reason):
        halfnode.BitcoinP2PProtocol.connectionLost(self, reason)
        log.info("P2P disconnected")

        global _connection
        _connection = None

    def broadcast_tx(self, txdata):
        '''Broadcast new transaction (as a hex stream) to trusted node'''
        tx = halfnode.msg_tx()
        tx.deserialize(StringIO.StringIO(binascii.unhexlify(txdata)))
        self.send_message(tx)
        
    def do_tx(self, message):
        '''Process incoming Bitcoin transaction'''        
        if not is_Abe:
            # Abe is not installed, parsing transactions is not available
            return
        
        message.tx.calc_sha256()
                
        for intx in message.tx.vin:
            pubkey = Abe.deserialize.extract_public_key(intx.scriptSig)
            if pubkey == '(None)':
                pubkey = None
                
            log.debug('in %s' % pubkey) 
            #print intx.prevout.n, intx.prevout.hash

        for outtx in message.tx.vout:
            pubkey = Abe.deserialize.extract_public_key(outtx.scriptPubKey)
            if pubkey == '(None)':
                pubkey = None

            log.debug('out %s %f' % (pubkey, outtx.nValue / 10**8.))
            
        log.debug('---')
        #pubkey = binascii.hexlify(message.tx.vout[0].scriptPubKey)
        #print pubkey, public_key_to_bc_address(pubkey)
#            sha256 = message.tx.sha256
#            pubkey = binascii.hexlify(message.tx.vout[0].scriptPubKey)
#            txlock.acquire()
#            tx.append([str(sha256), str(time.time()), str(self.dstaddr), pubkey])
#            txlock.release()

class P2PFactory(ReconnectingClientFactory):
    def startFactory(self):
        ReconnectingClientFactory.startFactory(self)

    def buildProtocol(self, addr):
        self.resetDelay()
        return P2PProtocol()

def shutdown():
    print "Shutting down P2P connection"
    print "TODO: Save memory pool"
    
def run(host):
    log.info("Connecting to trusted Bitcoin node at %s" % host)
    reactor.connectTCP(host, 8333, P2PFactory())
    reactor.addSystemEventTrigger('before', 'shutdown', shutdown)
