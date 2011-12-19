DEBUG = True

# Port used for Socket transport
LISTEN_SOCKET_TRANSPORT = 23232

# User agent used in HTTP requests (e.g. firstbits lookup)
USER_AGENT = 'YourServer/0.1'

try:
    ADMIN_PASSWORD = open('admin_password', 'r').read().strip()
except:
    print "File 'admin_password' not found, admin functionality in RPC disabled."
    ADMIN_PASSWORD = None # Admin functionality is disabled

'''
BITCOIN_TRUSTED_HOST = '127.0.0.1'
BITCOIN_TRUSTED_PORT = 8332
BITCOIN_TRUSTED_USER = 'marekp'
BITCOIN_TRUSTED_PASSWORD = 'brutalniheslo'
'''

'''
DATABASE_DRIVER = 'MySQLdb'
DATABASE_HOST = 'palatinus.cz'
DATABASE_DBNAME = 'marekp_bitcointe'
DATABASE_USER = 'marekp_bitcointe'
DATABASE_PASSWORD = '**empty**'
'''
