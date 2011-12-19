import json

from twisted.protocols.basic import LineReceiver
from twisted.internet import defer

import services
import custom_exceptions

class Protocol(LineReceiver):
    def _get_id(self):
        self.request_id += 1
        return self.request_id

    def connectionMade(self):
        self.request_id = 0    
        self.lookup_table = {}
    
    def writeJsonRequest(self, method, params):
        request_id = self._get_id()
        data = {'id': request_id, 'method': method, 'params': params}
        self.transport.write(json.dumps(data))
        return request_id
        
    def writeJsonResponse(self, request_id, data):
        data = {'id': request_id, 'result': data, 'error': None}
        self.transport.write(json.dumps(data))

    def writeJsonError(self, request_id, message, code=-1):
        data = {'id': request_id, 'result': None, 'error': (code, message)}
        self.transport.write(json.dumps(data))

    def writeGeneralError(self, message, code=-100):
        print message
        return self.writeJsonError(0, message, code)
    
    def process_result(self, res, msg_id):
        if res != None:
            self.writeJsonResponse(msg_id, res)

    def process_fail(self, exc, msg_id):
        self.writeJsonError(msg_id, exc.getBriefTraceback())

    def dataReceived(self, data):
        for line in data.splitlines(False):
            try:
                message = json.loads(line)
            except:
                self.writeGeneralError("Cannot decode message '%s'" % line)
                continue
            
            msg_id = message.get('id', 0)
            msg_method = message.get('method')
            msg_result = message.get('result')
            msg_error = message.get('error')
            msg_params = message.get('params')
                                            
            if msg_method:
                # It's a RPC call or simple message
                result = defer.maybeDeferred(services.ServiceFactory.call, msg_method, msg_params)
                result.addCallback(self.process_result, msg_id)
                result.addErrback(self.process_fail, msg_id)                
                
            elif msg_result != None or msg_error:
                # It's a RPC response
                # Perform lookup to the table of waiting requests.
               
                try:
                    d = self.lookup_table[msg_id]
                    del self.lookup_table[msg_id]
                except KeyError:
                    # When deferred object for given message ID isn't found, it's an error
                    raise custom_exceptions.ProtocolException("Lookup for deferred object for message ID '%s' failed." % msg_id)

                if msg_result != None:
                    d.callback(msg_result)
                else:
                    d.errback(custom_exceptions.RemoteServiceException(msg_error[0], msg_error[1]))
                    
            else:
                raise custom_exceptions.ProtocolException("Cannot handle message '%s'" % line)
            
    @defer.inlineCallbacks
    def rpc(self, method, params, expect_response=True):
        '''
            This method performs remote RPC call.

            If method should expect an response, it store
            request ID to lookup table and wait for corresponding
            response message.
        ''' 
        
        request_id = self.writeJsonRequest(method, params)
        
        if expect_response:
            d = defer.Deferred()
            self.lookup_table[request_id] = d
            response = (yield d)
            defer.returnValue(response)
            
            
class ClientProtocol(Protocol):
    def connectionMade(self):
        Protocol.connectionMade(self)
        self.factory.client = self
        if self.factory.on_connect:
            self.factory.on_connect.callback(True)
        
    def connectionLost(self, reason):
        self.factory.client = None
        Protocol.connectionLost(self, reason)
            