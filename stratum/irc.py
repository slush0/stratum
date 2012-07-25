from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
import random
import string

import custom_exceptions
import logger
log = logger.get_logger('irc')

# Reference to open IRC connection
_connection = None

def get_connection():
    if _connection:
        return _connection
    
    raise custom_exceptions.IrcClientException("IRC not connected")

class IrcLurker(irc.IRCClient):        
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.peers = {}
        
        global _connection
        _connection = self

    def get_peers(self):
        return self.peers.values()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        
        global _connection
        _connection = None

    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        log.info('Joined %s' % channel)
        
    #def dataReceived(self, data):
    #    print data
    #    irc.IRCClient.dataReceived(self, data.replace('\r', ''))
            
    def privmsg(self, user, channel, msg):
        user = user.split('!', 1)[0]
        
        if channel == self.nickname or msg.startswith(self.nickname + ":"):
            log.info("'%s': %s" % (user, msg))
            return
        
    #def action(self, user, channel, msg):
    #    user = user.split('!', 1)[0]
    #    print user, channel, msg
        
    def register(self, nickname, *args, **kwargs):
        self.setNick(nickname)
        self.sendLine("USER %s 0 * :%s" % (self.nickname, self.factory.hostname))
               
    def irc_RPL_NAMREPLY(self, prefix, params):
        for nick in params[3].split(' '):
            if not nick.startswith('S_'):
                continue
            
            if nick == self.nickname:
                continue
            
            self.sendLine("WHO %s" % nick)
                
    def irc_RPL_WHOREPLY(self, prefix, params):
        nickname = params[5]
        hostname = params[7].split(' ', 1)[1]
        log.debug("New peer '%s' (%s)" % (hostname, nickname))
        self.peers[nickname] = hostname
     
    def userJoined(self, nickname, channel):
        self.sendLine("WHO %s" % nickname)
        
    def userLeft(self, nickname, channel):
        self.userQuit(nickname)
        
    def userKicked(self, nickname, *args, **kwargs):
        self.userQuit(nickname)
        
    def userQuit(self, nickname, *args, **kwargs):
        try:
            hostname = self.peers[nickname]
            del self.peers[nickname]
            log.info("Peer '%s' (%s) disconnected" % (hostname, nickname))
        except:
            pass
        
    #def irc_unknown(self, prefix, command, params):
    #    print "UNKNOWN", prefix, command, params
        
class IrcLurkerFactory(protocol.ClientFactory):
    def __init__(self, channel, nickname, hostname):
        self.channel = channel
        self.nickname = nickname
        self.hostname = hostname

    def _random_string(self, N):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))

    def buildProtocol(self, addr):
        p = IrcLurker()
        p.factory = self
        p.nickname = "S_%s_%s" % (self.nickname, self._random_string(5))
        log.info("Using nickname '%s'" % p.nickname)
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        log.error("Connection lost")
        reactor.callLater(10, connector.connect)

    def clientConnectionFailed(self, connector, reason):
        log.error("Connection failed")
        reactor.callLater(10, connector.connect)

if __name__ == '__main__':
    # Example of using IRC bot
    reactor.connectTCP("irc.freenode.net", 6667, IrcLurkerFactory('#stratum-nodes', 'test', 'example.com'))
    reactor.run()