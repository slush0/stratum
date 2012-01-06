from twisted.internet import defer
from twisted.python import log
#import types
import re

import custom_exceptions

VENDOR_RE = re.compile(r'\[(.*)\]')

class ServiceFactory(object):
    registry = {} # Mapping service_type -> vendor -> cls
    
    @classmethod
    def _split_method(cls, method):
        '''Parses "some.service[vendor].method" string
        and returns 3-tuple with (service_type, vendor, rpc_method)'''
        
        # Splits the service type and method name
        (service_type, method_name) = method.rsplit('.', 1)
        vendor = None
        
        if '[' in service_type:
            # Use regular expression only when brackets found
            try:
                vendor = VENDOR_RE.search(service_type).group(1)
                service_type = service_type.replace('[%s]' % vendor, '')
            except:
                raise
                #raise custom_exceptions.ServiceNotFoundException("Invalid syntax in service name '%s'" % type_name[0])
            
        return (service_type, vendor, method_name)
    
    @classmethod
    def call(cls, method, params):
        (service_type, vendor, func) = cls._split_method(method)
                    
        try:
            func = cls.lookup(service_type, vendor=vendor)().__getattribute__(func)
            if not callable(func):
                raise
        except:
            raise custom_exceptions.MethodNotFoundException("Method '%s' not found for service '%s'" % (func, service_type))
        
        return func(*params)
        
    @classmethod
    def lookup(cls, service_type, vendor=None):
        # Lookup for service type provided by specific vendor
        if vendor:
            try:
                return cls.registry[service_type][vendor]
            except KeyError:
                raise custom_exceptions.ServiceNotFoundException("Class for given service type and vendor isn't registered")
        
        # Lookup for any vendor, prefer default one
        try:
            vendors = cls.registry[service_type]        
        except KeyError:
            raise custom_exceptions.ServiceNotFoundException("Class for given service type isn't registered")

        last_found = None        
        for _, _cls in vendors.items():
            last_found = _cls
            if last_found.is_default:
                return last_found
            
        if not last_found:
            raise custom_exceptions.ServiceNotFoundException("Class for given service type isn't registered")
        
        return last_found

    @classmethod
    def register_service(cls, _cls, meta):
        # Register service class to ServiceFactory
        service_type = meta.get('service_type')
        service_vendor = meta.get('service_vendor')
        is_default = meta.get('is_default')
           
        if str(_cls.__name__) in ('GenericService',):
            # str() is ugly hack, but it is avoiding circular references
            return
        
        if not service_type:
            raise custom_exceptions.MissingServiceTypeException("Service class '%s' is missing 'service_type' property." % _cls)

        if not service_vendor:
            raise custom_exceptions.MissingServiceVendorException("Service class '%s' is missing 'service_vendor' property." % _cls)

        if is_default == None:
            raise custom_exceptions.MissingServiceIsDefaultException("Service class '%s' is missing 'is_default' property." % _cls)
        
        if is_default:
            # Check if there's not any other default service
            
            try:
                current = cls.lookup(service_type)
                if current.is_default:
                    raise custom_exceptions.DefaultServiceAlreadyExistException("Default service already exists for type '%s'" % service_type)
            except custom_exceptions.ServiceNotFoundException:
                pass
        
        ServiceFactory.registry.setdefault(service_type, {})
        ServiceFactory.registry[service_type][service_vendor] = _cls

        log.msg("Registered %s for service '%s', vendor '%s' (default: %s)" % (_cls, service_type, service_vendor, is_default))

class SignatureWrapper(object):
    '''This wrapper around any object indicate that caller want to sign given object'''
    def __init__(self, obj, sign=None, sign_algo=None, sign_id=None):
        self.obj = obj
        self.sign = sign
        self.sign_algo = sign_algo
        self.sign_id = sign_id
        
    def get_object(self):
        return self.obj
    
    def get_sign(self):
        if self.sign:
            return (self.sign, self.sign_algo, self.sign_id)
        
        raise custom_exceptions.SignatureException("Signature not found")
    
def signature(func):
    '''Decorate RPC method result with server's signature.
    This decorator can be chained with Deferred or inlineCallbacks, thanks to _sign_generator() hack.'''

    def _sign_generator(iterator):
        '''Iterate thru generator object, detects BaseException
        and inject SignatureWrapper into exception's value (=result of inner method).
        This is black magic because of decorating inlineCallbacks methods.
        See returnValue documentation for understanding this:
        http://twistedmatrix.com/documents/11.0.0/api/twisted.internet.defer.html#returnValue'''
    
        for i in iterator:
            try:
                iterator.send((yield i))
            except BaseException as exc:
                exc.value = SignatureWrapper(exc.value)
                raise

    def _sign_deferred(res):
        return SignatureWrapper(res)
    
    def _sign_failure(fail):
        fail.value = SignatureWrapper(fail.value)
        return fail
    
    def inner(*args, **kwargs):        
        ret = func(*args, **kwargs)
        if isinstance(ret, defer.Deferred):
            ret.addCallback(_sign_deferred)
            ret.addErrback(_sign_failure)
            return ret
        #elif isinstance(ret, types.GeneratorType):
        #    return _sign_generator(ret)
        else:
            return SignatureWrapper(ret)
    return inner

def synchronous(func):
    '''Run given method synchronously in separate thread and return the result.'''
    # Local import, because services itself aren't depending on twisted
    from twisted.internet import threads
    def inner(*args, **kwargs):
        return threads.deferToThread(func, *args, **kwargs)
    return inner
    
class ServiceMetaclass(type):
    def __init__(cls, name, bases, _dict):
        super(ServiceMetaclass, cls).__init__(name, bases, _dict)
        ServiceFactory.register_service(cls, _dict)
        
class GenericService(object):
    __metaclass__ = ServiceMetaclass
    service_type = None
    service_vendor = None
    is_default = None
    
    def ping(self, payload):
        return payload
    
class ServiceDiscovery(GenericService):
    service_type = 'discovery'
    service_vendor = 'Stratum'
    is_default = True
    
    def list_services(self):
        return ServiceFactory.registry.keys()
    
    def list_vendors(self, service_type):
        return ServiceFactory.registry[service_type].keys()
    
    def list_methods(self, service_name):
        # Accepts also vendors in square brackets: firstbits[firstbits.com]
        
        # Parse service type and vendor. We don't care about the method name,
        # but _split_method needs full path to some RPC method.
        (service_type, vendor, _) = ServiceFactory._split_method("%s.foo" % service_name)
        service = ServiceFactory.lookup(service_type, vendor)
        out = []
        
        for name, obj in service.__dict__.items():
            
            if name.startswith('_'):
                continue
            
            if not callable(obj):
                continue

            out.append(name)
        
        return out
    
    def list_params(self, *args):
        out = []
        for arg in args:
            (service_type, vendor, method) = ServiceFactory._split_method(arg)
            service = ServiceFactory.lookup(service_type, vendor)
            
            # Load params and helper text from method attributes
            func = service.__dict__[method]
            params = getattr(func, 'params', None)
            help_text = getattr(func, 'help_text', None)
            
            out.append((arg, help_text, params,))
        return out
    list_params.help_text = "Accepts name of methods and returns their description and available parameters. Example: 'firstbits.resolve', 'firstbits.create'"
    list_params.params = [('method1', 'string', 'Method to lookup for description and parameters.'),
                          ('methodN' ,'string', 'Another method to lookup')]