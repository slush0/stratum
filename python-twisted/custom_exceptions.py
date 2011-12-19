class ProtocolException(Exception):
    pass

class ServiceException(Exception):
    pass

class RemoteServiceException(Exception):
    pass

class MissingServiceTypeException(ServiceException):
    pass

class MissingServiceVendorException(ServiceException):
    pass

class MissingServiceIsDefaultException(ServiceException):
    pass

class DefaultServiceAlreadyExistException(ServiceException):
    pass

class ServiceNotFoundException(ServiceException):
    pass

class MethodNotFoundException(ServiceException):
    pass