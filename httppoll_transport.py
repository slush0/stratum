from zope.interface import Interface, Attribute, implements
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.python.components import registerAdapter
from twisted.web.server import Session

from storage import Storage
from protocol import process_request
import settings

class IProxyStorage(Interface):
    storage = Attribute("Storage for services")

class ProxyStorage(object):
    implements(IProxyStorage)
    def __init__(self, session):
        self.storage = Storage()

registerAdapter(ProxyStorage, Session, IProxyStorage)

class Root(Resource):
    isLeaf = True
    
    def __init__(self, debug=False):
        Resource.__init__(self)
        self.debug = debug # This class acts as a 'factory', debug is used by Protocol
        
    def render_GET(self, request):
        return "Welcome to %s server. Use HTTP POST to talk with the server." % settings.USER_AGENT
    
    def render_POST(self, request):
        self.request = request
        self.storage = IProxyStorage(request.getSession()).storage
               
        request.setHeader('content-type', 'application/json')
        request.setHeader('server', settings.USER_AGENT)

        #for h in request.requestHeaders.getAllRawHeaders():
        #    print h
            
        data = request.content.read()   
        process_request(self, self, data, self._finish)
        
        return NOT_DONE_YET

    def write(self, data):
        '''Act as a proxy method for Protocol.transport.write'''
        self.request.write(data)
        
    def _finish(self, *args):
        self.request.finish()