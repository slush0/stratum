from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

import settings_server as settings

class ResponseCruncher(Protocol):
    '''Helper for get_page()'''
    def __init__(self, finished):
        self.finished = finished
        self.response = ""
        
    def dataReceived(self, bytes):
        self.response += bytes

    def connectionLost(self, reason):
        self.finished.callback(self.response)
        
@defer.inlineCallbacks        
def get_page(url, method='GET', payload=None):
    '''Downloads the page from given URL, using asynchronous networking'''
    agent = Agent(reactor)

    response = (yield agent.request(
        method,
        str(url),
        Headers({'User-Agent': [settings.USER_AGENT,]}),
        payload))

    try:        
        finished = defer.Deferred()
        (yield response).deliverBody(ResponseCruncher(finished))
    except:
        raise Exception("Downloading page '%s' failed" % url)

    defer.returnValue((yield finished))