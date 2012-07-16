class ProtocolException(Exception):
    pass

class ServiceException(Exception):
    pass

class UnauthorizedException(Exception):
    pass

class SignatureException(Exception):
    pass

class PubsubException(ServiceException):
    pass

class IrcClientException(Exception):
    pass

class SigningNotAvailableException(SignatureException):
    pass

class UnknownSignatureIdException(SignatureException):
    pass

class UnknownSignatureAlgorithmException(SignatureException):
    pass

class SignatureVerificationFailedException(SignatureException):
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