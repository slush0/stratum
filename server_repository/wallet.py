from services import GenericService, no_response

class WalletService(GenericService):
    service_type = 'wallet'
    service_vendor = 'Electrum'
    is_default = True
    
    def import_seed(self, seed):
        return True
    
    def add_pubkey(self, pubkey):
        return True
    
    def remove_pubkey(self, pubkey):
        return True
    
    def create_transaction(self, address, amount):
        return ""
    
    def save(self):
        return True
    
    def load(self):
        return True
    