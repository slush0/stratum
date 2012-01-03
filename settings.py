DEBUG = True

# How many threads use for synchronous methods (services)
THREAD_POOL_SIZE = 30

# Port used for Socket transport
LISTEN_SOCKET_TRANSPORT = 23232

# Port used for HTTP Poll transport
LISTEN_HTTPPOLL_TRANSPORT = 8000

# Port used for HTTPS Poll transport
LISTEN_HTTPSPOLL_TRANSPORT = 8001

# Private key and certification file for SSL layer
SSL_PRIVKEY = 'privkey.pem'
SSL_CACERT = 'cacert.pem'

# Keepalive for HTTP transport sessions (at this time for both poll and push)
HTTP_SESSION_TIMEOUT = 30

# User agent used in HTTP requests (e.g. firstbits lookup)
USER_AGENT = 'YourServer/0.1'

try:
    ADMIN_PASSWORD = open('admin_password', 'r').read().strip()
except:
    print "File 'admin_password' not found, admin functionality in RPC disabled."
    ADMIN_PASSWORD = None # Admin functionality is disabled

try:
    import signature
    SIGNING_KEY = signature.load_privkey_pem('signing_key.pem')
except:
    print "Loading 'signing_key.pem' failed, protocol messages cannot be signed."
    SIGNING_KEY = None # Signing is disabled

BITCOIN_TRUSTED_HOST = '109.74.195.194'
BITCOIN_TRUSTED_PORT = 8332
BITCOIN_TRUSTED_USER = 'marekp'
BITCOIN_TRUSTED_PASSWORD = 'brutalniheslo'

'''
DATABASE_DRIVER = 'MySQLdb'
DATABASE_HOST = 'palatinus.cz'
DATABASE_DBNAME = 'marekp_bitcointe'
DATABASE_USER = 'marekp_bitcointe'
DATABASE_PASSWORD = '**empty**'
'''
