from twisted.internet import defer
import json

from services import GenericService
from helpers import get_page
        
class TxradarService(GenericService):
    service_type = 'txradar'
    service_vendor = 'transactionradar.com'
    is_default = True

    @defer.inlineCallbacks    
    def search(self, tx_hash):
        result = (yield get_page('http://transactionradar.com/api/v1/tx/%s' % tx_hash))
        defer.returnValue(json.loads(result))