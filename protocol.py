import json
import time

from twisted.protocols.basic import LineReceiver
from twisted.internet import defer

import services
import signature
import custom_exceptions
import connection_registry

class Protocol(LineReceiver, connection_registry.ConnectionRegistryMixin):
    def _get_id(self):
        self.request_id += 1
        return self.request_id

    def connectionMade(self):
        self.wait_to_finish = None
        self.request_counter = 0
        self.request_id = 0    
        self.lookup_table = {}
    
    def writeJsonRequest(self, method, params, is_notification=False):
        request_id = None if is_notification else self._get_id() 
        data = {'id': request_id, 'method': method, 'params': params}
        if self.factory.debug:
            print "<", data        
        self.transport.write("%s\n" % json.dumps(data))
        return request_id
        
    def writeJsonResponse(self, data, message_id, use_signature=False, sign_method='', sign_params=[]):
        if self.factory.debug:
            print "<", data        
        
        if use_signature:
            serialized = signature.jsonrpc_dumps_sign(self.factory.signing_key, False,\
                message_id, int(time.time()), sign_method, sign_params, data, None)
        else:
            serialized = json.dumps({'id': message_id, 'result': data, 'error': None})
            
        self.transport.write("%s\n" % serialized)
        self.dec_request_counter()

    def writeJsonError(self, code, message, message_id, use_signature=False, sign_method='', sign_params=[]):       
        if use_signature:
            serialized = signature.jsonrpc_dumps_sign(self.factory.signing_key, False,\
                message_id, int(time.time()), sign_method, sign_params, None, (code, message))
        else:
            serialized = json.dumps({'id': message_id, 'result': None, 'error': (code, message)})
            
        self.transport.write("%s\n" % serialized)
        self.dec_request_counter()

    def writeGeneralError(self, message, code=-1):
        print message
        return self.writeJsonError(code, message, 0)
    
    def dec_request_counter(self):
        self.request_counter -= 1
        if self.request_counter <= 0 and self.wait_to_finish:
            self.wait_to_finish.callback(True)
            self.wait_to_finish = None
            
    def process_response(self, data, message_id, sign_method, sign_params):
        if isinstance(data, services.SignatureWrapper):
            # Sign response object with server's private key
            self.writeJsonResponse(data.get_object(), message_id, True, sign_method, sign_params)
        else:
            self.writeJsonResponse(data, message_id)
            
    def process_failure(self, failure, message_id, sign_method, sign_params):
        if isinstance(failure.value, services.SignatureWrapper):
            # Strip SignatureWrapper object
            failure.value = failure.value.get_object()
            
            code = -1
            message = failure.getBriefTraceback()
            self.writeJsonError(code, message, message_id, True, sign_method, sign_params)
        else:
            code = -1
            message = failure.getBriefTraceback()
            self.writeJsonError(code, message, message_id)
        
    def dataReceived(self, data, return_deferred=False):
        if not self.wait_to_finish:
            self.wait_to_finish = defer.Deferred()
        
        lines = data.splitlines(False)
        self.request_counter += len(lines)
        
        for line in lines:
            try:
                message = json.loads(line)
            except:
                self.writeGeneralError("Cannot decode message '%s'" % line)
                continue
            
            if self.factory.debug:
                print ">", message
            
            msg_id = message.get('id', 0)
            msg_method = message.get('method')
            msg_params = message.get('params')
            msg_result = message.get('result')
            msg_error = message.get('error')
                                            
            if msg_method:
                # It's a RPC call or notification
                result = defer.maybeDeferred(services.ServiceFactory.call, msg_method, msg_params)
                if msg_id == None:
                    # It's notification, don't expect the response
                    self.dec_request_counter()
                else:
                    # It's a RPC call
                    result.addCallback(self.process_response, msg_id, msg_method, msg_params)
                    result.addErrback(self.process_failure, msg_id, msg_method, msg_params)                
                
            elif msg_result != None or msg_error:
                # It's a RPC response
                # Perform lookup to the table of waiting requests.
               
                self.dec_request_counter()
               
                print self.lookup_table
                try:
                    meta = self.lookup_table[msg_id]
                    del self.lookup_table[msg_id]
                except KeyError:
                    # When deferred object for given message ID isn't found, it's an error
                    raise custom_exceptions.ProtocolException("Lookup for deferred object for message ID '%s' failed." % msg_id)

                if msg_result != None:
                    meta['defer'].callback(msg_result)
                else:
                    meta['defer'].errback(custom_exceptions.RemoteServiceException(msg_error[0], msg_error[1]))
                
            else:
                raise custom_exceptions.ProtocolException("Cannot handle message '%s'" % line)
    
        if return_deferred:
            return self.wait_to_finish
          
    @defer.inlineCallbacks
    def rpc_multi(self, methods):
        '''
        Expect list of three-tuples (method, list-of-params, expect_response).
        '''
        
        responses = []
        for i, m in list(enumerate(methods)):
            
            method, params, is_notification = m
            request_id = self.writeJsonRequest(method, params, is_notification)
        
            if is_notification:
                responses.append(None)
            else:
                def on_response(response, i):
                    print response, i
                    responses[i] = response
                
                d = defer.Deferred()
                d.addCallback(on_response, i)               
                self.lookup_table[request_id] = {'defer': d, 'method': method, 'params': params}
                responses.append(d) # Add defer placeholder instead of result
         
        # Wait until all placeholders will be replaced by real responses
        for i in range(len(responses)):
            if isinstance(responses[i], defer.Deferred):
                yield responses[i]
            
        # Translate dictionary into list
        #responses = [ responses_dict[i] for i in range(len(responses_dict.keys())) ]
        defer.returnValue(responses)
        
    @defer.inlineCallbacks
    def rpc(self, method, params, is_notification=False):
        '''
            This method performs remote RPC call.

            If method should expect an response, it store
            request ID to lookup table and wait for corresponding
            response message.
        ''' 

        request_id = self.writeJsonRequest(method, params, is_notification)

        if not is_notification:
            d = defer.Deferred()
            self.lookup_table[request_id] = {'defer': d, 'method': method, 'params': params}
            response = (yield d)
            defer.returnValue(response)
            
class ClientProtocol(Protocol):
    def connectionMade(self):
        Protocol.connectionMade(self)
        self.factory.client = self
        if self.factory.on_connect:
            self.factory.on_connect.callback(True)
            self.factory.on_connect = None
        
    def connectionLost(self, reason):
        self.factory.client = None
        Protocol.connectionLost(self, reason)
