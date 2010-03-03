from crud import ExtDirectCRUD

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
    Very simple class decorator, just initialize the object. All the magic it's in the
    __init__ method of BaseExtDirectCRUD. So, you must ensure that your class
    inherit from ExtDirectCRUD.
    """    
    def decorator(klass, action):        
        action = action or klass.__name__    
        i = klass(provider, action, login_required, permission)
        
        return klass        
        
    return lambda klass: decorator(klass, action)
