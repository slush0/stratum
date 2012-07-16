from twisted.internet import defer
from twisted.internet import reactor
from twisted.names import client
import random
import time

from services import GenericService, signature, synchronous
import pubsub

import logger
log = logger.get_logger('example')

class ExampleService(GenericService):
    service_type = 'example'
    service_vendor = 'Stratum'
    is_default = True

    def hello_world(self):
        return "Hello world!"

    @signature
    def ping(self, payload):
        return payload
    
    @synchronous
    def synchronous(self, how_long):
        '''This can use blocking calls, because it runs in separate thread'''
        for x in range(int(how_long)):
            time.sleep(1)
        return 'Request finished in %d seconds' % how_long
            
    def throw_exception(self):
        raise Exception("Some error")
   
    @signature
    def throw_signed_exception(self):
        raise Exception("Some error")
    
'''
class TimeSubscription(pubsub.Subscription):
    def filter(self, t):
        if t % self.params['period'] == 0:
            return True
        return False
'''
     
class TimeSubscription(pubsub.Subscription):
    event = 'example.pubsub.time_event'
    def filter(self, t):
        return t % self.params.get('period', 1) == 0
        
class PubsubExampleService(GenericService):
    service_type = 'example.pubsub'
    service_vendor = 'Stratum'
    is_default = True
    
    def _setup(self):
        self._emit_time_event()
    
    @pubsub.subscribe
    def subscribe(self, period):
        return TimeSubscription(period=period)
    
    @pubsub.unsubscribe
    def unsubscribe(self, period):
        return TimeSubscription(period=period)
    
    def _emit_time_event(self):
        # This will emit a publish event,
        # so all subscribed clients will receive
        # the notification
        
        t = time.time()
        TimeSubscription.emit(int(t))
        reactor.callLater(1, self._emit_time_event)
        
        # Let's print some nice stats
        cnt = pubsub.Pubsub.get_subscription_count('example.pubsub.time_event')
        if cnt:
            log.info("Example event emitted in %.03f sec to %d subscribers" % (time.time() - t, cnt))