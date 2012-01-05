from twisted.internet import defer
from twisted.internet import reactor
import hashlib

import settings 
from services import GenericService, signature, synchronous
import helpers
import custom_exceptions

def admin(func):
    def inner(*args, **kwargs):
        if not len(args):
            raise custom_exceptions.UnauthorizedException("Missing password")
        
        if not settings.ADMIN_PASSWORD_SHA256:
            raise custom_exceptions.UnauthorizedException("Admin password not set, RPC call disabled")
        
        (password, args) = (args[1], [args[0],] + list(args[2:]))  

        if hashlib.sha256(password).hexdigest() != settings.ADMIN_PASSWORD_SHA256:
            raise custom_exceptions.UnauthorizedException("Wrong password")
              
        return func(*args, **kwargs)
    return inner

class NodeService(GenericService):
    service_type = 'node'
    service_vendor = 'Electrum'
    is_default = True
        
    @signature
    @defer.inlineCallbacks
    def get_peers(self):
        # FIXME: Own implementation
        peers = []
        for peer in (yield helpers.ask_old_server('peers')):
            peers.append({
                'trusted': True,
                'weight': 1,
                'ipv4': peer[0],
                'ipv6': None,
                'hostname': peer[1],      
            })
        defer.returnValue(peers)
    
    @admin
    def stop(self):
        print "node.stop() received, stopping server..."
        reactor.callLater(1, reactor.stop)
        return True
