import custom_exceptions

class ServiceFactory(object):
    registry = {} # Mapping service_type -> vendor -> cls

    @classmethod
    def _split_method(cls, method):
        '''Returns tuple with (service_type, rpc_method)'''
        x = method.rsplit('.', 1)
        return (x[0], x[1])
    
    @classmethod
    def call(cls, method, params, vendor=None):
        (service_type, func) = cls._split_method(method)
        
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

        print "Registered %s for service '%s', vendor '%s' (default: %s)" % (_cls, service_type, service_vendor, is_default)

def no_response(func):
    '''Supress any result from inner method (even exceptions!)'''
    def inner(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            pass
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
    service_vendor = 'Electrum'
    is_default = True
    
    def list_services(self):
        return ServiceFactory.registry.keys()
    
    def list_vendors(self, service_type):
        return ServiceFactory.registry[service_type].keys()
    
    def list_methods(self, service_type, vendor):
        service = ServiceFactory.lookup(service_type, vendor)
        out = []
        
        for name, obj in service.__dict__.items():
            
            if name.startswith('_'):
                continue
            
            if not callable(obj):
                continue

            out.append(name)
        
        return out