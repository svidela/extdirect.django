
def remoting(action, provider, name=None, len=0, form_handler=False, \
             login_required=False, permission=None):
    """
    Decorator to register a function for a given `action` and `provider`.
    `provider` must be an instance of ExtRemotingProvider
    """
    def decorator(func):    
        provider.register(action, func, name, len, form_handler, login_required, permission)
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
