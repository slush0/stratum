import json
#import jsonical
import time

from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet import defer
from twisted.python.failure import Failure

#import services
import event_handler
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
    
    def __init__(self, event_handler=event_handler.GenericEventHandler()):
        self.event_handler = event_handler
        
    def _get_id(self):
        self.request_id += 1
        return self.request_id

    def connectionMade(self):
        self.request_id = 0    
        self.lookup_table = {}
        self.event_handler = self.factory.event_handler()
    
        log.debug("Connected %s" % self.transport.getPeer().host)
        connection_registry.ConnectionRegistry.add_connection(self)
    
    def transport_write(self, data):
        '''Overwrite this if transport needs some extra care about data written
        to the socket, like adding message format in websocket''' 
        self.transport.write(data)
        
    def connectionLost(self, reason):
        connection_registry.ConnectionRegistry.remove_connection(self)
       
    def writeJsonRequest(self, method, params, is_notification=False):
        request_id = None if is_notification else self._get_id() 
        serialized = json.dumps({'id': request_id, 'method': method, 'params': params})

        if self.factory.debug:
            log.debug("< %s" % serialized)
                    
        self.transport_write("%s\n" % serialized)
        return request_id
        
    def writeJsonResponse(self, data, message_id, use_signature=False, sign_method='', sign_params=[]):        
        if use_signature:
            serialized = signature.jsonrpc_dumps_sign(self.factory.signing_key, self.factory.signing_id, False,\
                message_id, sign_method, sign_params, data, None)
        else:
            serialized = json.dumps({'id': message_id, 'result': data, 'error': None})
            
        if self.factory.debug:
            log.debug("< %s" % serialized)        

        self.transport_write("%s\n" % serialized)

    def writeJsonError(self, code, message, traceback, message_id, use_signature=False, sign_method='', sign_params=[]):       
        if use_signature:
            serialized = signature.jsonrpc_dumps_sign(self.factory.signing_key, self.factory.signing_id, False,\
                message_id, sign_method, sign_params, None, (code, message, traceback))
        else:
            serialized = json.dumps({'id': message_id, 'result': None, 'error': (code, message, traceback)})
            
        self.transport_write("%s\n" % serialized)

    def writeGeneralError(self, message, code=-1):
        log.error(message)
        return self.writeJsonError(code, message, None, None)
            
    def process_response(self, data, message_id, sign_method, sign_params, request_counter):
        self.writeJsonResponse(data.result, message_id, data.sign, sign_method, sign_params)
        request_counter.decrease()
            
    def process_failure(self, failure, message_id, sign_method, sign_params, request_counter):
        sign = False
        code = -1
        #if isinstance(failure.value, services.ResultObject):
        #    # Strip ResultObject
        #    sign = failure.value.sign
        #    failure.value = failure.value.result
        
        traceback = failure.getBriefTraceback()
        self.writeJsonError(code, str(failure.value), str(traceback), message_id, sign, sign_method, sign_params)    
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
            try:
                result = self.event_handler.handle_event(msg_method, msg_params, connection_ref=self)
            except Exception as exc:
                failure = Failure()
                self.process_failure(failure, msg_id, msg_method, msg_params, request_counter)

            else:    
                if msg_id == None:
                    # It's notification, don't expect the response
                    request_counter.decrease()
                else:
                    # It's a RPC call
                    result.addCallback(self.process_response, msg_id, msg_method, msg_params, request_counter)
                    result.addErrback(self.process_failure, msg_id, msg_method, msg_params, request_counter)
            
        elif msg_id: #(msg_result != None or msg_error) and msg_id:
            # It's a RPC response
            # Perform lookup to the table of waiting requests.
           
            request_counter.decrease()
           
            try:
                meta = self.lookup_table[msg_id]
                del self.lookup_table[msg_id]
            except KeyError:
                # When deferred object for given message ID isn't found, it's an error
                raise custom_exceptions.ProtocolException("Lookup for deferred object for message ID '%s' failed." % msg_id)

            # If there's an error, handle it as errback
            # If both result and error are null, handle it as a success with blank result
            if msg_error != None:
                meta['defer'].errback(custom_exceptions.RemoteServiceException(msg_error[0], msg_error[1], msg_error[2]))
            else:
                meta['defer'].callback(msg_result)
            
        else:
            request_counter.decrease()
            raise custom_exceptions.ProtocolException("Cannot handle message '%s'" % line)
          
    def rpc(self, method, params, is_notification=False):
        '''
            This method performs remote RPC call.

            If method should expect an response, it store
            request ID to lookup table and wait for corresponding
            response message.
        ''' 

        request_id = self.writeJsonRequest(method, params, is_notification)

        if is_notification:
            return

        d = defer.Deferred()
        self.lookup_table[request_id] = {'defer': d, 'method': method, 'params': params}
        return d
                    
class ClientProtocol(Protocol):
    def connectionMade(self):
        Protocol.connectionMade(self)
        self.factory.client = self
                
        if self.factory.timeout_handler:
            self.factory.timeout_handler.cancel()
            self.factory.timeout_handler = None

        if isinstance(getattr(self.factory, 'after_connect', None), list):
            log.debug("Resuming connection: %s" % self.factory.after_connect)
            for cmd in self.factory.after_connect:
                self.rpc(cmd[0], cmd[1])
            
        if self.factory.on_connect:
            self.factory.on_connect.callback(self)
            self.factory.on_connect = None
            
        #d = self.rpc('node.get_peers', [])
        #d.addCallback(self.factory.add_peers)
                
    def connectionLost(self, reason):
        self.factory.client = None

        if self.factory.timeout_handler:
            self.factory.timeout_handler.cancel()
            self.factory.timeout_handler = None
        
        if self.factory.on_disconnect:
            self.factory.on_disconnect.callback(True)
            self.factory.on_disconnect = None
            
        Protocol.connectionLost(self, reason)
