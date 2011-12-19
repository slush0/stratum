from twisted.internet import defer

from services import GenericService, no_response
from helpers import get_page

import settings_server as settings
        
class FirstbitsService(GenericService):
    service_type = 'firstbits'
    service_vendor = 'firstbits.com'
    is_default = True

    @defer.inlineCallbacks    
    def _process(self, address):     
        result = (yield get_page('http://firstbits.com/api/?a=%s' % address)).strip()
        defer.returnValue(result)
    
    def create(self, address):
        # TODO: Full address validation (try to do a checksum etc)
        if len(address) < 24 or address[0] != '1':
            raise Exception("Invalid address")
        
        return self._process(address)
            
    def resolve(self, firstbits):
        if len(firstbits) > 24 or firstbits[0] != '1':
            raise Exception("Invalid firstbits")

        return self._process(firstbits)
    
