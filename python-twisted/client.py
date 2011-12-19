from twisted.internet import reactor
from twisted.internet import defer

import custom_exceptions
from socket_transport import SocketTransportClientFactory
    
@defer.inlineCallbacks
def main():
    # Try to connect to remote server
    d = defer.Deferred()
    f = SocketTransportClientFactory('localhost', 23232, d)
    yield d # Wait to on_connect event
    
    try:
        # Example of full RPC call, including proper exception handling
        print (yield f.rpc('firstbits.ping', ['nazdar',]))
    except custom_exceptions.RemoteServiceException as exc:
        print "RPC call failed", str(exc) 

    # Example of service discover, this will print all known services, their vendors
    # and available methods on remote server
    print (yield f.rpc('discovery.list_services', []))
    print (yield f.rpc('discovery.list_vendors', ['firstbits',]))
    print (yield f.rpc('discovery.list_methods', ['firstbits', 'firstbits.com',]))

    # Example call of firstbits service
    print (yield f.rpc('firstbits.resolve', ['1MarekM',]))
    print (yield f.rpc('firstbits.create', ['1MarekMKDKRb6PEeHeVuiCGayk9avyBGBB',]))
    
    reactor.stop()

main()
reactor.run()
