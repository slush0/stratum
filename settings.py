'''
This is example configuration for Stratum server.
Please rename it to settings.py and fill correct values.
'''

DEBUG = True

LOGDIR = 'log/'
LOGFILE= 'stratum.log'
LOGLEVEL = 'DEBUG'

# How many threads use for synchronous methods (services)
THREAD_POOL_SIZE = 30

# Port used for Socket transport
LISTEN_SOCKET_TRANSPORT = 3333

# Port used for HTTP Poll transport
LISTEN_HTTPPOLL_TRANSPORT = 8000

# Port used for HTTPS Poll transport
LISTEN_HTTPSPOLL_TRANSPORT = 4430

# Private key and certification file for SSL layer
SSL_PRIVKEY = 'privkey.pem'
SSL_CACERT = 'cacert.pem'

# Keepalive for HTTP transport sessions (at this time for both poll and push)
HTTP_SESSION_TIMEOUT = 11

# User agent used in HTTP requests (e.g. firstbits lookup)
USER_AGENT = 'Stratum/0.1'

BITCOIN_TRUSTED_HOST = '109.74.195.194'
BITCOIN_TRUSTED_PORT = 8332
BITCOIN_TRUSTED_USER = 'stratum'
BITCOIN_TRUSTED_PASSWORD = '***somepassword***'

#ADMIN_PASSWORD_SHA256 = None # Admin functionality is disabled
ADMIN_PASSWORD_SHA256 = '9e6c0c1db1e0dfb3fa5159deb4ecd9715b3c8cd6b06bd4a3ad77e9a8c5694219' # SHA256 of the password

SIGNING_ID = 'stratum.bitcoin.cz'
SIGNING_KEY = 'signing_key.pem'

'''
DATABASE_DRIVER = 'MySQLdb'
DATABASE_HOST = 'palatinus.cz'
DATABASE_DBNAME = 'marekp_bitcointe'
DATABASE_USER = 'marekp_bitcointe'
DATABASE_PASSWORD = '**empty**'
'''
