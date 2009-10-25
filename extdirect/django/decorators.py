
def remoting(provider, action=None, name=None, len=0, form_handler=False, \
             login_required=False, permission=None):
    """
    Decorator to register a function for a given `action` and `provider`.
    `provider` must be an instance of ExtRemotingProvider
    """    
    def decorator(func):        
        provider.register(func, action, name, len, form_handler, login_required, permission)
        return func
        
    return decorator

def polling(provider, login_required=False, permission=None):
    """
    Decorator to register a function for a `provider`.
    `provider` must be an instance of ExtPollingProvider
    """
    def decorator(func):
        provider.register(func, login_required, permission)
        return func
    
    return decorator

def crud(provider, action=None, login_required=False, permission=None):
    """    
    """    
    def decorator(klass, action):
        i = klass()
        
        action = action or klass.__name__
        
        provider.register(i.create, action, 'create', 1, False, login_required, permission)
        provider.register(i.read, action, 'read', 1, False, login_required, permission)
        provider.register(i.update, action, 'update', 2, False, login_required, permission)
        provider.register(i.destroy, action, 'destroy', 1, False, login_required, permission)
        
        return klass
        
    return lambda klass: decorator(klass, action)
