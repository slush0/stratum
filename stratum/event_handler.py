class GenericEventHandler(object):
    def handle_event(self, msg_method, msg_params, connection_ref):
        print "Other side called method", msg_method, "with params", msg_params
        raise NotImplemented