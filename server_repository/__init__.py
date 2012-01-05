from . import blockchain
from . import firstbits
from . import wallet
from . import node
from . import txradar

'''
Mapping of new Electrum protocol to old one:
    done blockchain.block.get_blocknum() -> b
    done blockchain.address.get_history(address) -> h
    done blockchain.transaction.broadcast(tx) -> tx
    
    done node.get_peers -> peers
    done node.stop -> stop
    
    poll -> blockchain.block.subscribe, blockchain.address.subscribe
    
    x load
    x clear_cache
    x get_cache
        
    x session
    x new_session
    x update_session
'''