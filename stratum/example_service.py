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
    hello_world.help_text = "Returns string 'Hello world!'"
    hello_world.params = []

    @signature
    def ping(self, payload):
        return payload
    ping.help_text = "Returns signed message with the payload given by the client."
    ping.params = [('payload', 'mixed', 'This payload will be sent back to the client.'),]
    
    @synchronous
    def synchronous(self, how_long):
        '''This can use blocking calls, because it runs in separate thread'''
        for _ in range(int(how_long)):
            time.sleep(1)
        return 'Request finished in %d seconds' % how_long
    synchronous.help_text = "Run time consuming algorithm in server's threadpool and return the result when it finish."
    synchronous.params = [('how_long', 'int', 'For how many seconds the algorithm should run.'),]
            
    def throw_exception(self):
        raise Exception("Some error")
    throw_exception.help_text = "Throw an exception and send error result to the client."
    throw_exception.params = []
   
    @signature
    def throw_signed_exception(self):
        raise Exception("Some error")
    throw_signed_exception.help_text = "Throw an exception and send signed error result to the client."
    throw_signed_exception.params = []
    
class TimeSubscription(pubsub.Subscription):
    event = 'example.pubsub.time_event'
    
    def process(self, t):
        # Process must return list of parameters for notification
        # or None if notification should not be send 
        if t % self.params.get('period', 1) == 0:
            return (t,)
        
    def after_subscribe(self, _):
        # Some objects want to fire up notification or other
        # action directly after client subscribes.
        # after_subscribe is the right place for such logic
        pass
        
class PubsubExampleService(GenericService):
    service_type = 'example.pubsub'
    service_vendor = 'Stratum'
    is_default = True
    
    def _setup(self):
        self._emit_time_event()
    
    @pubsub.subscribe
    def subscribe(self, period):
        return TimeSubscription(period=period)
    subscribe.help_text = "Subscribe client for receiving current server's unix timestamp."
    subscribe.params = [('period', 'int', 'Broadcast to the client only if timestamp%period==0. Use 1 for receiving an event in every second.'),]
    
    @pubsub.unsubscribe
    def unsubscribe(self, subscription_key):#period):
        return subscription_key
    unsubscribe.help_text = "Stop broadcasting unix timestampt to the client."
    unsubscribe.params = [('subscription_key', 'string', 'Key obtained by calling of subscribe method.'),]
    
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