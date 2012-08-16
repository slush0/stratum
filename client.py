from twisted.internet import reactor
from twisted.internet import defer

#import custom_exceptions
from stratum.socket_transport import SocketTransportClientFactory
from stratum.services import GenericService, ServiceEventHandler

import time

class PubsubReceivingService(GenericService):
    service_type = 'example.pubsub'
    service_vendor = 'custom'
    is_default = True
    
    def time_event(self, t):
        print "Received notification for the time_event !!!", t
        
@defer.inlineCallbacks
def unsubscribe(f, event, key):
    print "Unsubscribed:", (yield f.rpc('example.pubsub.unsubscribe', [key,]))
    reactor.stop()
    
@defer.inlineCallbacks
def main():
    debug = False

    # Try to connect to remote server
    d = defer.Deferred()
    hostname = 'california.stratum.bitcoin.cz'
    #hostname = 'localhost'
    f = SocketTransportClientFactory(hostname, 3333,
                allow_trusted=True,
                allow_untrusted=False,
                debug=debug,
                signing_key=None,
                signing_id=None,
                on_connect=d,
                event_handler=ServiceEventHandler)
    yield d # Wait to on_connect event

    (event, subscription_key) = (yield f.subscribe('example.pubsub.subscribe', [1,]))
    print "Subscribed:", event, subscription_key
    reactor.callLater(3, unsubscribe, f, event, subscription_key)
    
    print (yield f.rpc('discovery.list_services', []))
    #print (yield f.rpc('discovery.list_methods', ['example']))
    #print (yield f.rpc('discovery.list_params', ['example.ping']))

    print (yield f.rpc('example.ping', ['testing payload']))
    '''
    s = time.time()
    x = 10
    for x in range(x):
        (yield f.rpc('node.ping', ['hi',]))

    print float(x) / (time.time() - s)
    '''
    #print (yield f.rpc('blockchain.transaction.broadcast', ['01000000016e71be76a49eac1d1f55113e4a581ea21a33e94a17453f6a0f3624db0b43b101000000008b48304502207e1fd0a8a8051fb21561df5d9d0e3ad0f3ced2b51e90ff1cebc85406a654cfaf022100bc7d3cf9a93959ff80953272d45fbd5cbdb8800874db0858783547ecef19c2ce014104e6a069738d8e8491a8abd3bed7d303c9b2dc3792173a18483653036fd74a5100fc6ee327b6a82b3df79005f101b88496988fa414af32df11fff3e96d53d26d03ffffffff0180969800000000001976a914e1c9b052561cf0a1da9ee3175df7d5a2d7ff7dd488ac00000000']))

    '''
    print (yield f.rpc_multi([
                 ['blockchain.block[Electrum].get_blocknum', [], False],
                 ['node.get_peers', [], False],
                 ['firstbits.create', ['1MarekMKDKRb6PEeHeVuiCGayk9avyBGBB',], False],
                 ['firstbits.create', ['1MarekMKDKRb6PEeHeVuiCGayk9avyBGBB',], False],
                 ['node.ping', ['test'], False],
                ]))
    '''

    '''
    print (yield f.rpc('blockchain.block.get_blocknum', []))
    #print (yield f.rpc('node.get_peers', []))

    try:
        # Example of full RPC call, including proper exception handling
        print (yield f.rpc('firstbits[firstbits.com].ping', ['nazdar',]))
    except custom_exceptions.RemoteServiceException as exc:
        print "RPC call failed", str(exc) 

    # Example of service discover, this will print all known services, their vendors
    # and available methods on remote server
    print (yield f.rpc('discovery.list_services', []))
    print (yield f.rpc('discovery.list_vendors', ['firstbits',]))
    print (yield f.rpc('discovery.list_methods', ['firstbits[firstbits.com]',]))

    # Example call of firstbits service
    print (yield f.rpc('firstbits.resolve', ['1MarekM',]))
    print (yield f.rpc('firstbits.create', ['1MarekMKDKRb6PEeHeVuiCGayk9avyBGBB',]))
    '''
    #reactor.stop()
    
main()
reactor.run()
