import weakref
from connection_registry import ConnectionRegistry
import custom_exceptions
import hashlib

def subscribe(func):
    '''Decorator detect Subscription object in result and subscribe connection'''
    def inner(self, *args, **kwargs):
        subs = func(self, *args, **kwargs)
        return Pubsub.subscribe(self._connection_ref(), subs)
    return inner

def unsubscribe(func):
    '''Decorator detect Subscription object in result and unsubscribe connection'''
    def inner(self, *args, **kwargs):
        subs = func(self, *args, **kwargs)
        if isinstance(subs, Subscription):
            return Pubsub.unsubscribe(self._connection_ref(), subscription=subs)
        else:
            return Pubsub.unsubscribe(self._connection_ref(), key=subs)
    return inner

class Subscription(object):
    def __init__(self, event=None, **params):
        if hasattr(self, 'event'):
            if event:
                raise Exception("Event name already defined in Subscription object")
        else:
            if not event:
                raise Exception("Please define event name in constructor")
            else:
                self.event = event
            
        self.params = params
        self.connection_ref = None
            
    def filter(self, *args, **kwargs):
        return True

    def process(self, *args, **kwargs):
        return args
            
    def get_key(self):
        '''This is an identifier for current subscription. It is sent to the client,
        so result should not contain any sensitive information.'''
        return hashlib.md5(str((self.event, self.params))).hexdigest()
    
    def get_session(self):
        '''Connection session may be useful in filter or process functions'''
        return ConnectionRegistry.get_session(self.connection_ref())
        
    @classmethod
    def emit(cls, *args, **kwargs):
        if not hasattr(cls, 'event'):
            raise Exception("Subscription.emit() can be used only for subclasses with filled 'event' class variable.")
        return Pubsub.emit(cls.event, *args, **kwargs)
        
    def _emit(self, *args, **kwargs):
        if not self.filter(*args, **kwargs):
            # Subscription don't pass this args
            return
            
        conn = self.connection_ref()
        if conn == None:
            # Connection is closed
            return

        conn.writeJsonRequest(self.event, self.process(*args, **kwargs), is_notification=True)
            
    def __eq__(self, other):
        return (isinstance(other, Subscription) and other.get_key() == self.get_key())
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
class Pubsub(object):
    __subscriptions = {}
    
    @classmethod
    def subscribe(cls, connection, subscription):
        if connection == None:
            raise custom_exceptions.PubsubException("Subscriber not connected")
        
        key = subscription.get_key()
        session = ConnectionRegistry.get_session(connection)
        if session == None:
            raise custom_exceptions.PubsubException("No session found")
        
        subscription.connection_ref = weakref.ref(connection)
        session['subscriptions'][key] = subscription
        
        cls.__subscriptions.setdefault(subscription.event, weakref.WeakValueDictionary())
        cls.__subscriptions[subscription.event][key] = subscription
        return (subscription.event, key)
    
    @classmethod
    def unsubscribe(cls, connection, subscription=None, key=None):
        if connection == None:
            raise custom_exceptions.PubsubException("Subscriber not connected")
        
        session = ConnectionRegistry.get_session(connection)
        if session == None:
            raise custom_exceptions.PubsubException("No session found")
        
        if subscription:
            key = subscription.get_key()

        try:
            # Subscription don't need to be removed from cls.__subscriptions,
            # because it uses weak reference there.
            del session['subscriptions'][key]
        except KeyError:
            print "Warning: Cannot remove subscription from connection session"
            return False
            
        return True
        
    @classmethod
    def get_subscription_count(cls, event):
        return len(cls.__subscriptions.get(event, {}))
    
    @classmethod
    def emit(cls, event, *args, **kwargs):
        for subscription in cls.__subscriptions.get(event, weakref.WeakValueDictionary()).itervaluerefs():
            subscription = subscription()
            if subscription == None:
                # Subscriber is no more connected
                continue
                        
            subscription._emit(*args, **kwargs)