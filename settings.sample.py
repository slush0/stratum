'''
This is example configuration for Stratum server.
Please rename it to settings.py and fill correct values.

Dependencies (FIXME: write real howto):
*  ecdsa (signatures)
*  twisted-words (IRC bot) 
'''

# ******************** GENERAL SETTINGS ***************

# Enable some verbose debug (logging requests and responses).
DEBUG = True

# Destination for application logs, files rotated once per day.
LOGDIR = 'log/'

# Main application log file.
LOGFILE = 'stratum.log'

# Possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'DEBUG'

# How many threads use for synchronous methods (services).
# 30 is enough for small installation, for real usage
# it should be slightly more, say 100-300.
THREAD_POOL_SIZE = 30

# ******************** TRANSPORTS *********************

# Hostname or external IP to expose
HOSTNAME = 'stratum.example.com'

# Port used for Socket transport. Use 'None' for disabling the transport.
LISTEN_SOCKET_TRANSPORT = 3333

# Port used for HTTP Poll transport. Use 'None' for disabling the transport
LISTEN_HTTP_TRANSPORT = 80

# Port used for HTTPS Poll transport
LISTEN_HTTPS_TRANSPORT = 443

# ******************** SSL SETTINGS ******************

# Private key and certification file for SSL protected transports
SSL_PRIVKEY = 'privkey.pem'
SSL_CACERT = 'cacert.pem'

# ******************** HTTP SETTINGS *****************

# Keepalive for HTTP transport sessions (at this time for both poll and push)
# High value leads to higher memory usage (all sessions are stored in memory ATM).
# Low value leads to more frequent session reinitializing (like downloading address history).
HTTP_SESSION_TIMEOUT = 3600 # in seconds

# User agent used in HTTP requests (for both HTTP transports and for proxy calls from services)
USER_AGENT = 'Stratum/0.1'

# Hostname and credentials for one trusted Bitcoin node ("Satoshi's client").
# Stratum uses both P2P port (which is 8333 already) and RPC port
BITCOIN_TRUSTED_HOST = '127.0.0.1'
BITCOIN_TRUSTED_PORT = 8332
BITCOIN_TRUSTED_USER = 'stratum'
BITCOIN_TRUSTED_PASSWORD = '***somepassword***'

# Use "echo '<yourpassword>' | sha256sum | cut -f1 -d' ' "
# for calculating SHA256 of your preferred password
ADMIN_PASSWORD_SHA256 = None # Admin functionality is disabled
#ADMIN_PASSWORD_SHA256 = '9e6c0c1db1e0dfb3fa5159deb4ecd9715b3c8cd6b06bd4a3ad77e9a8c5694219' # SHA256 of the password

# Use "./signature.py > signing_key.pem" to generate unique signing key for your server
SIGNING_KEY = None # Message signing is disabled
#SIGNING_KEY = 'signing_key.pem'

# Origin of signed messages. Provide some unique string,
# ideally URL where users can find some information about your identity
SIGNING_ID = None
#SIGNING_ID = 'stratum.somedomain.com' # Use custom string
#SIGNING_ID = HOSTNAME # Use hostname as the signing ID

# *********************** PEER CONFIGURATION *************

#IRC_NICK = None # Skip IRC registration
IRC_NICK = "stratum" # Use nickname of your choice

# Which hostname / external IP expose in IRC room
# This should be official HOSTNAME for normal operation.
IRC_HOSTNAME = HOSTNAME

# Don't change this unless you're creating private Stratum cloud.
IRC_SERVER = 'irc.freenode.net'
IRC_ROOM = '#stratum-nodes'
IRC_PORT = 6667

# Hardcoded list of Stratum nodes for clients to switch when this node is not available.
PEERS = [
    {
        'hostname': 'stratum.bitcoin.cz',
        'trusted': True, # This node is trustworthy
        'weight': -1, # Higher number means higher priority for selection.
                      # -1 will work mostly as a backup when other servers won't work.
                      # (IRC peers have weight=0 automatically).
    },
]


'''
DATABASE_DRIVER = 'MySQLdb'
DATABASE_HOST = 'palatinus.cz'
DATABASE_DBNAME = 'marekp_bitcointe'
DATABASE_USER = 'marekp_bitcointe'
DATABASE_PASSWORD = '**empty**'
'''
