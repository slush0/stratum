from twisted.internet import defer
from twisted.internet import reactor

import settings 
from services import GenericService, no_response
import helpers
import custom_exceptions

def admin(func):
    def inner(*args, **kwargs):
        if not len(args):
            raise custom_exceptions.UnauthorizedException("Missing password")
        
        if not settings.ADMIN_PASSWORD:
            raise custom_exceptions.UnauthorizedException("Admin password not set, RPC call disabled")
        
        (password, args) = (args[1], [args[0],] + list(args[2:]))  

        if password != settings.ADMIN_PASSWORD:
            raise custom_exceptions.UnauthorizedException("Wrong password")
              
        return func(*args, **kwargs)
    return inner

class NodeService(GenericService):
    service_type = 'node'
    service_vendor = 'Electrum'
    is_default = True
    
    @defer.inlineCallbacks
    def get_peers(self):
        # FIXME: Own implementation
        print (yield helpers.ask_old_server('peers'))

        defer.returnValue(True)    
    
    @admin
    def stop(self):
        print "node.stop() received, stopping server..."
        reactor.callLater(1, reactor.stop)
        return True
