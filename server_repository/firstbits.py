from twisted.internet import defer

from services import GenericService, signature
from helpers import get_page

import settings
        
class FirstbitsService(GenericService):
    service_type = 'firstbits'
    service_vendor = 'firstbits.com'
    is_default = True

    @defer.inlineCallbacks    
    def _process(self, address):     
        result = (yield get_page('http://firstbits.com/api/?a=%s' % address)).strip()
        defer.returnValue(result)
    
    @defer.inlineCallbacks
    def create(self, address):
        # TODO: Full address validation (try to do a checksum etc)
        if len(address) < 24 or address[0] != '1':
            raise Exception("Invalid address")
        
        firstbits = (yield self._process(address))
        
        # Simple sanity check
        if address.lower().startswith(firstbits.lower()):
            defer.returnValue(firstbits)
        else:
            raise Exception("Firstbits lookup failed")
    create.params = [('address', 'string', "String containing full Bitcoin address. Example: '1MarekMKDKRb6PEeHeVuiCGayk9avyBGBB'. Don't hesitate to send small donation here :).")]
    create.help_text = 'Create firstbits shortcut from full Bitcoin address.'
    
    @defer.inlineCallbacks
    def resolve(self, firstbits):
        if len(firstbits) > 24 or firstbits[0] != '1':
            raise Exception("Invalid firstbits")

        address = (yield self._process(firstbits))
        
        # Simple sanity check
        if address.lower().startswith(firstbits.lower()):
            defer.returnValue(address)
        else:
            raise Exception("Firstbits lookup failed")
    resolve.params = [('firstbits', 'string', "String containing shortened Bitcoin address. Example: '1marekMKDK'")]
    resolve.help_text = 'Resolve full Bitcoin address from given firstbits.'
