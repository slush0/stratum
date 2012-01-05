from twisted.internet import defer

from services import GenericService
import helpers
import settings

import p2pnode
p2pnode.run(settings.BITCOIN_TRUSTED_HOST)

class BlockchainBlockService(GenericService):
    service_type = 'blockchain.block'
    service_vendor = 'Electrum'
    is_default = True
    
    def subscribe(self):
        return True
    
    def unsubscribe(self):
        return True

    def get_blocknum(self):
        # FIXME: Own implementation
        return helpers.ask_old_server('b')
    
class BlockchainAddressService(GenericService):
    service_type = 'blockchain.address'
    service_vendor = 'Electrum'
    is_default = True
    
    def subscribe(self, address):
        return True
    
    def unsubscribe(self, address):
        return True

    def get_history(self, address):
        # FIXME: Own implementation
        return helpers.ask_old_server('h', address)
    
    def get_balance(self, address):
        # FIXME: Own implementation
        return helpers.ask_old_server('b', address)
    
class BlockchainTransactionService(GenericService):
    service_type = 'blockchain.transaction'
    service_vendor = 'Electrum'
    is_default = True
    
    def subscribe(self):
        return True
    
    def unsubscribe(self):
        return True

    def guess_fee(self):
        # FIXME: Blockchain analysis
        return 0.0005
    
    def broadcast(self, transaction):
        p2pnode.get_connection().broadcast_tx(transaction)
        return True

    def get(self, hash):
        raise NotImplemented
