import json
import jsonical
import time

from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import defer

import services
import signature
import custom_exceptions
import connection_registry
import logger

log = logger.get_logger('protocol')

class RequestCounter(object):
    def __init__(self, deferred=None):
        self.deferred = deferred
        self.counter = 0
        
    def set_count(self, cnt):
        self.counter = cnt
        
    def decrease(self):
        self.counter -= 1
        if self.counter <= 0 and self.deferred:
            self.deferred.callback(True)
            self.deferred = None

class Protocol(LineOnlyReceiver):
    delimiter = '\n'
    
    def _get_id(self):
        self.request_id += 1
        return self.request_id

    def connectionMade(self):
        self.request_id = 0    
        self.lookup_table = {}
    
        log.debug("Connected %s" % self.transport.getPeer().host)
        connection_registry.ConnectionRegistry.add_connection(self)
    
    def connectionLost(self, reason):
        connection_registry.ConnectionRegistry.remove_connection(self)

    def writeJsonRequest(self, method, params, is_notification=False):
        request_id = None if is_notification else self._get_id() 
        serialized = jsonical.dumps({'id': request_id, 'method': method, 'params': params})

        if self.factory.debug:
            log.debug("< %s" % serialized)
                    
        self.transport.write("%s\n" % serialized)
        return request_id
        
    def writeJsonResponse(self, data, message_id, use_signature=False, sign_method='', sign_params=[]):        
        if use_signature:
            serialized = signature.jsonrpc_dumps_sign(self.factory.signing_key, self.factory.signing_id, False,\
                message_id, sign_method, sign_params, data, None)
        else:
            serialized = jsonical.dumps({'id': message_id, 'result': data, 'error': None})
            
        if self.factory.debug:
            log.debug("< %s" % serialized)        

        self.transport.write("%s\n" % serialized)

    def writeJsonError(self, code, message, message_id, use_signature=False, sign_method='', sign_params=[]):       
        if use_signature:
            serialized = signature.jsonrpc_dumps_sign(self.factory.signing_key, self.factoruy.signing_id, False,\
                message_id, int(time.time()), sign_method, sign_params, None, (code, message))
        else:
            serialized = jsonical.dumps({'id': message_id, 'result': None, 'error': (code, message)})
            
        self.transport.write("%s\n" % serialized)

    def writeGeneralError(self, message, code=-1):
        log.error(message)
        return self.writeJsonError(code, message, None)
            
    def process_response(self, data, message_id, sign_method, sign_params, request_counter):
        if isinstance(data, services.SignatureWrapper):
            # Sign response object with server's private key
            # TODO: Proxy signature details if presented in SignatureWrapper
            self.writeJsonResponse(data.get_object(), message_id, True, sign_method, sign_params)
        else:
            self.writeJsonResponse(data, message_id)
            
        request_counter.decrease()
            
    def process_failure(self, failure, message_id, sign_method, sign_params, request_counter):
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
            
        request_counter.decrease()
        
    def dataReceived(self, data, request_counter=RequestCounter()):
        '''Original code from Twisted, hacked for request_counter proxying.
        request_counter is hack for HTTP transport, didn't found cleaner solution how
        to indicate end of request processing in asynchronous manner.
        
        TODO: This would deserve some unit test to be sure that future twisted versions
        will work nicely with this.'''
        
        lines  = (self._buffer+data).split(self.delimiter)
        self._buffer = lines.pop(-1)
        request_counter.set_count(len(lines))
        
        for line in lines:
            if self.transport.disconnecting:
                return
            if len(line) > self.MAX_LENGTH:
                return self.lineLengthExceeded(line)
            else:
                self.lineReceived(line, request_counter)
        if len(self._buffer) > self.MAX_LENGTH:
            return self.lineLengthExceeded(self._buffer)        
        
    def lineReceived(self, line, request_counter):
        try:
            message = json.loads(line)
        except:
            #self.writeGeneralError("Cannot decode message '%s'" % line)
            raise custom_exceptions.ProtocolException("Cannot decode message '%s'" % line)
        
        if self.factory.debug:
            log.debug("> %s" % message)
        
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
                request_counter.decrease()
            else:
                # It's a RPC call
                result.addCallback(self.process_response, msg_id, msg_method, msg_params, request_counter)
                result.addErrback(self.process_failure, msg_id, msg_method, msg_params, request_counter)
            
        elif (msg_result != None or msg_error) and msg_id:
            # It's a RPC response
            # Perform lookup to the table of waiting requests.
           
            request_counter.decrease()
           
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
