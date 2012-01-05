from twisted.web.resource import Resource
from twisted.web.server import Session, NOT_DONE_YET
from twisted.internet import defer
from twisted.python.failure import Failure
import hashlib
import json

import helpers
import semaphore
#from storage import Storage
from protocol import Protocol, RequestCounter
import settings

import logger
log = logger.get_logger('http_transport')

class Transport(object):
    def __init__(self, session_id, lock):
        self.buffer = []
        self.session_id = session_id
        self.lock = lock
        self.push_url = None
        self.peer = None
        
    def getPeer(self):
        return self.peer
    
    def write(self, data):
        self.buffer.append(data)
            
        if not self.lock.is_locked() and self.push_url:
            # Push the buffer to callback URL
            # TODO: Buffer responses and perform callbacks in batches
            self.push_buffer()
            
    def push_buffer(self):
        '''Push the content of the buffer into callback URL'''
        if not self.push_url:
            return
        
        buffer = self.fetch_buffer()
        
        # FIXME: Don't expect any response
        helpers.get_page(self.push_url, method='POST',
                         headers={"content-type": "application/stratum",
                                  "x-session-id": self.session_id},
                         payload=buffer)
        
    def fetch_buffer(self):
        ret = ''.join(self.buffer)
        self.buffer = []
        return ret
    
    def set_push_url(self, url):
        self.push_url = url

class HttpSession(Session):
    sessionTimeout = settings.HTTP_SESSION_TIMEOUT
    
    def __init__(self, *args, **kwargs):
        Session.__init__(self, *args, **kwargs)
        #self.storage = Storage()
        
        # Reference to connection object (Protocol instance)
        self.protocol = None
        
        # Synchronizing object for avoiding race condition on session
        self.lock = semaphore.Semaphore(1)

        # Output buffering
        self.transport = Transport(self.uid, self.lock)
                        
        # Setup cleanup method on session expiration
        self.notifyOnExpire(lambda: HttpSession.on_expire(self))

    @classmethod
    def on_expire(cls, sess_obj):
        # FIXME: Close protocol connection
        print "EXPIRING SESSION", sess_obj
        
        if sess_obj.protocol:
            sess_obj.protocol.connectionLost(Failure(Exception("HTTP session closed")))
            
        sess_obj.protocol = None
            
class Root(Resource):
    isLeaf = True
    
    def __init__(self, debug=False, signing_key=None):
        Resource.__init__(self)
        self.signing_key = signing_key
        self.debug = debug # This class acts as a 'factory', debug is used by Protocol
        
    def render_GET(self, request):
        return "Welcome to %s server. Use HTTP POST to talk with the server." % settings.USER_AGENT
        
    def render_POST(self, request):
        session = request.getSession()
        
        l = session.lock.acquire()
        l.addCallback(self._perform_request, request, session)
        return NOT_DONE_YET
        
    def _perform_request(self, _, request, session):
        request.setHeader('content-type', 'application/stratum')
        request.setHeader('server', settings.USER_AGENT)
        request.setHeader('x-session-timeout', session.sessionTimeout)
          
        # Update client's IP address     
        session.transport.peer = request.getHost()
 
        if request.getHeader('content-type') != 'application/stratum':
            session.transport.write("%s\n" % json.dumps({'id': None, 'result': None, 'error': (-1, "Content-type must be 'application/stratum'. See http://stratum.bitcoin.cz for more info.")}))
            self._finish(None, request, session.transport, session.lock)
            return
        
        if not session.protocol:            
            # Build a "protocol connection"
            proto = Protocol()
            proto.transport = session.transport
            proto.factory = self
            proto.connectionMade()
            session.protocol = proto
        else:
            proto = session.protocol
 
        # Update callback URL if presented
        callback_url = request.getHeader('x-callback-url')
        if callback_url:
            session.transport.push_url = callback_url 
                  
        data = request.content.read()
        wait = defer.Deferred()
        wait.addCallback(self._finish, request, session.transport, session.lock)
        proto.dataReceived(data, request_counter=RequestCounter(wait))
        

    @classmethod        
    def _finish(cls, _, request, transport, lock):
        # First parameter is callback result; not used here
        
        data = transport.fetch_buffer()
        request.setHeader('content-length', len(data))
        request.setHeader('content-md5', hashlib.md5(data).hexdigest())
        request.setHeader('x-content-sha256', hashlib.sha256(data).hexdigest())
        request.write(data)
        request.finish()
        lock.release()