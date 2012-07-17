def setup():
    '''
        This will import modules config_default and config and move their variables
        into current module (variables in config have higher priority than config_default).
        Thanks to this, you can import settings anywhere in the application and you'll get
        actual application settings.
    '''
    
    def read_values(cfg):
        for varname in cfg.__dict__.keys():
            if varname.startswith('__'):
                continue
            
            value = getattr(cfg, varname)
            yield (varname, value)

    import config_default
    import config
            
    import sys
    module = sys.modules[__name__]
    
    for name,value in read_values(config_default):
        module.__dict__[name] = value

    changes = {}
    for name,value in read_values(config):
        if value != module.__dict__[name]:
            changes[name] = value
        module.__dict__[name] = value

    if module.__dict__['DEBUG'] and changes:
        print "----------------"
        print "Custom settings:"
        for k, v in changes.items():
            print k, ":", v
        print "----------------"
        
setup()
