from twisted.internet import defer
from twisted.internet import reactor
from twisted.names import client

import hashlib

import settings 
from services import GenericService, signature, synchronous
import custom_exceptions
import irc

import logger
log = logger.get_logger('service.node')

def admin(func):
    def inner(*args, **kwargs):
        if not len(args):
            raise custom_exceptions.UnauthorizedException("Missing password")
        
        if not settings.ADMIN_PASSWORD_SHA256:
            raise custom_exceptions.UnauthorizedException("Admin password not set, RPC call disabled")
        
        (password, args) = (args[1], [args[0],] + list(args[2:]))  

        if hashlib.sha256(password).hexdigest() != settings.ADMIN_PASSWORD_SHA256:
            raise custom_exceptions.UnauthorizedException("Wrong password")
              
        return func(*args, **kwargs)
    return inner

class NodeService(GenericService):
    service_type = 'node'
    service_vendor = 'Electrum'
    is_default = True
        
    @signature
    @defer.inlineCallbacks
    def get_peers(self):
        # FIXME: Cache result/DNS lookup
        peers = []
        
        # Include hardcoded peers
        for peer in settings.PEERS:

            if not peer.get('ipv4'):
                try:
                    peer['ipv4'] = (yield client.getHostByName(peer['hostname']))
                except Exception:
                    log.error("Failed to resolve hostname '%s'" % peer['hostname'])
                    continue
                
            peers.append({
                'hostname': peer['hostname'],
                'trusted': peer.get('trusted', False),
                'weight': peer.get('weight', 0),
                'ipv4': peer.get('ipv4'),
                'ipv6': peer.get('ipv6'),
            })
        
        if settings.IRC_NICK:
            try:
                irc_peers = irc.get_connection().get_peers()
            except custom_exceptions.IrcClientException:
                log.error("Retrieving IRC peers failed")
                irc_peers = []
                
            for peer in irc_peers:

                try:
                    ipv4 = (yield client.getHostByName(peer))
                except Exception:
                    log.error("Failed to resolve hostname '%s'" % peer['hostname'])
                    continue
                
                peers.append({
                    'hostname': peer,
                    'trusted': False,
                    'weight': 0,
                    'ipv4': ipv4,
                    'ipv6': None,
                })
        
        defer.returnValue(peers)
    
    @admin
    def stop(self):
        print "node.stop() received, stopping server..."
        reactor.callLater(1, reactor.stop)
        return True
