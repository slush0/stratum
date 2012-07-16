import weakref
from connection_registry import ConnectionRegistry
import custom_exceptions

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
        return Pubsub.unsubscribe(self._connection_ref(), subs)
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
        return (isinstance(other, Subscription) and other.event == self.event and other.params == self.params)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
class Pubsub(object):
    __subscriptions = {}
    
    @classmethod
    def subscribe(cls, connection, subscription):
        if connection == None:
            raise custom_exceptions.PubsubException("Subscriber not connected")
        
        session = ConnectionRegistry.get_session(connection)
        if session == None:
            raise custom_exceptions.PubsubException("No session found")
        
        subscription.connection_ref = weakref.ref(connection)
        session['subscriptions'].append(subscription)
        
        cls.__subscriptions.setdefault(subscription.event, weakref.WeakKeyDictionary())
        cls.__subscriptions[subscription.event][subscription] = None
        return True
    
    @classmethod
    def unsubscribe(cls, connection, subscription):
        if connection == None:
            raise custom_exceptions.PubsubException("Subscriber not connected")
        
        session = ConnectionRegistry.get_session(connection)
        if session == None:
            raise custom_exceptions.PubsubException("No session found")
        
        for s in session['subscriptions']:
            if s != subscription: # This uses custom __eq__ method
                continue
                
            try:
                session['subscriptions'].remove(s)
            except:
                print "Warning: Cannot remove subscription from connection session"
                
            try:
                del cls.__subscriptions[subscription.event][s]
            except:
                print "Warning: Cannot remove subscription from Pubsub structure"
        
            break
        
        return True
        
    @classmethod
    def get_subscription_count(cls, event):
        return len(cls.__subscriptions.get(event, {}))
    
    @classmethod
    def emit(cls, event, *args, **kwargs):
        for subscription in cls.__subscriptions.get(event, weakref.WeakKeyDictionary()).iterkeyrefs():
            subscription = subscription()
            if subscription == None:
                # Subscriber is no more connected
                continue
                        
            subscription._emit(*args, **kwargs)