import sys, traceback

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

SCRIPT = """
Ext.onReady(function() {
    Ext.Direct.addProvider(%s);
});    
"""

class ExtDirectProvider(object):
    """
    Abstract class for different ExtDirect Providers implementations
    """
    
    def __init__(self, url, type, id=None):        
        self.type = type        
        self.url = url
        self.id = id
    
    @property
    def _config(self):
        """
        Return the config object to add a new Ext.DirectProvider
        It must allow to be dumped using simplejson.dumps
        """
        raise NotImplementedError
        
    def register(self, **kw):
        """
        Register a new function/method in this Provider.
        The arguments to this function will depend on the subclasses that
        implement it
        """
        raise NotImplementedError
        
    def router(self, request):
        """
        Entry point for ExtDirect requests.
        Subclasses must implement this method and make the rpc call.
        
        You will have to add an urlpattern to your urls.py
        pointing to this method. Something like::
        
            remote_provider = ExtDirectProvider('/some-url/', ...)
            urlpatterns = patterns(
                ...,
                (r'^some-url/$', remote_provider.router),
                ...
            )
        """
        raise NotImplementedError
    
    def script(self, request):
        """
        Return a HttpResponse with the javascript code needed
        to register the DirectProvider in Ext.
        
        You will have to add an urlpattern to your urls.py
        pointing to this method. Something like::
        
            remote_provider = ExtDirectProvider('/some-url/', ...)
            urlpatterns = patterns(
                ...,
                (r'^myprovider.js/$', remote_provider.script),
                ...
            )
        """
        config = simplejson.dumps(self._config)
        js =  SCRIPT % config
                
        return HttpResponse(js, mimetype='text/javascript')
    
class ExtRemotingProvider(ExtDirectProvider):
    """
    ExtDirect RemotingProvider implementation
    """
    
    type = 'remoting'
    
    def __init__(self, namespace, url, id=None, descriptor='Descriptor'):
        super(ExtRemotingProvider, self).__init__(url, self.type, id)
        
        self.namespace = namespace        
        self.actions = {}
        self.descriptor = descriptor


    def api(self, request):
        conf = self._config
        descriptor = self.namespace + '.' + self.descriptor
        
        if request.GET.has_key('format') and request.GET['format'] == 'json':
            conf['descriptor'] = descriptor
            mimetype = 'application/json'
            response = simplejson.dumps(conf)
        else:
            response = """
Ext.ns('%s');
%s = %s
""" % (self.namespace, descriptor, simplejson.dumps(self._config))
            mimetype = 'text/javascript'
            
        return HttpResponse(response, mimetype=mimetype)
        
    @property
    def _config(self):
        config = {
            'url'       : self.url,
            'namespace' : self.namespace,
            'type'      : self.type,
            'actions'   : {}                
        }
        
        for action, methods in self.actions.items():
            config['actions'][action] = []
            
            for func, info in methods.items():
                method = dict(name=func, len=info['len'], formHandler=info['form_handler'])
                config['actions'][action].append(method)
        
        if self.id:
            config['id'] = self.id
        
        return config    

    def register(self, method, action=None, name=None, len=0, form_handler=False, \
                 login_required=False, permission=None):
        
        if not action:
            action = method.__module__.replace('.', '_')
            
        if not self.actions.has_key(action):
            #first time
            self.actions[action] = {}
        
        #if name it's None, we use the real function name.
        name = name or method.__name__  
        self.actions[action][name] = dict(func=method,
                                          len=len,
                                          form_handler=form_handler,
                                          login_required=login_required,
                                          permission=permission)        
        
    def dispatcher(self, request, extdirect_req):
        """
        Parse the ExtDirect specification an call
        the function with the `request` instance.
        
        If the `request` didn't come from an Ext Form, then the
        parameters recieved will be added to the `request` in the
        `extdirect_post_data` attribute.
        """
        
        action = extdirect_req['action']
        method = extdirect_req['method']
        
        func = self.actions[action][method]['func']        
        
        data = None
        if not extdirect_req.get('isForm'):
            data = extdirect_req.pop('data')
        
        #the response object will be the same recieved but without `data`.
        #we will add the `result` later.
        response = extdirect_req
        
        #Checks for login or permissions required
        login_required = self.actions[action][method]['login_required']
        if(login_required):            
            if not request.user.is_authenticated():                
                response['result'] = dict(success=False, message='You must be authenticated to run this method.')
                return response
            
        permission = self.actions[action][method]['permission']
        if(permission):            
            if not request.user.has_perm(permission):                
                response['result'] = dict(success=False, messsage='You need `%s` permission to run this method' % permission)
                return response
                
        if data:
            #this is a simple hack to convert all the dictionaries keys
            #to strings instead of unicodes. {u'key': u'value'} --> {'key': u'value'}
            #This is needed if the function called want to pass the dictionaries as kw arguments.
            params = []
            for param in data:
                if isinstance(param, dict):
                    param = dict(map(lambda x: (str(x[0]), x[1]), param.items()))
                params.append(param)
                
            #Add the `extdirect_post_data` attribute to the request instance
            request.extdirect_post_data = params
            
        if extdirect_req.get('isForm'):
            extdirect_post_data = request.POST.copy()
            extdirect_post_data.pop('extAction')
            extdirect_post_data.pop('extMethod')
            extdirect_post_data.pop('extTID')
            extdirect_post_data.pop('extType')
            extdirect_post_data.pop('extUpload')
            
            request.extdirect_post_data = extdirect_post_data
        
        #finally, call the function passing the `request`
        try:
            response['result'] = func(request)
        except Exception, e:            
            if settings.DEBUG:
                etype, evalue, etb = sys.exc_info()
                response['type'] = 'exception'                
                response['message'] = traceback.format_exception_only(etype, evalue)[0]
                response['where'] = traceback.extract_tb(etb)[-1]
            else:
                raise e
        
        return response
        
    def router(self, request):
        """
        Check if the request came from a Form POST and call
        the dispatcher for every ExtDirect request recieved.
        """
        if request.POST.has_key('extAction'):
            extdirect_request = dict(
                action = request.POST['extAction'],
                method = request.POST['extMethod'],
                tid = request.POST['extTID'],
                type = request.POST['extType'],
                isForm = True
            )        
        elif request.raw_post_data:
            extdirect_request = simplejson.loads(request.raw_post_data)            
            
        else:
            return HttpResponseBadRequest('Invalid request')

        if isinstance(extdirect_request, list):
            #call in batch
            response = []
            for single_request in extdirect_request:
                response.append(self.dispatcher(request, single_request))

        elif isinstance(extdirect_request, dict):
           #single call
           response = self.dispatcher(request, extdirect_request)
        
        if request.POST.get('extUpload', False):
            #http://www.extjs.com/deploy/dev/docs/?class=Ext.form.BasicForm#Ext.form.BasicForm-fileUpload
            mimetype = 'text/html'
        else:
            mimetype = 'application/json'
            
        return HttpResponse(simplejson.dumps(response, cls=DjangoJSONEncoder), mimetype=mimetype)
        

class ExtPollingProvider(ExtDirectProvider):
    
    type = 'polling'
    
    def __init__(self, url, event, func=None, login_required=False, permission=None, id=None):
        super(ExtPollingProvider, self).__init__(url, self.type, id)
        
        self.func = func
        self.event = event
        
        self.login_required = login_required
        self.permission = permission
        
    @property
    def _config(self):
        config = {
            'url'   : self.url,
            'type'  : self.type        
        }
        if self.id:
            config['id'] = self.id
            
        return config
        
    def register(self, func, login_required=False, permission=None):
        self.func = func
        self.login_required = login_required
        self.permission = permission
    
    def router(self, request):
        response = {}

        if(self.login_required):            
            if not request.user.is_authenticated():
                response['type'] = 'event'
                response['data'] = 'You must be authenticated to run this method.'
                response['name'] = self.event
                return HttpResponse(simplejson.dumps(response, cls=DjangoJSONEncoder), mimetype='application/json')
                
        if(self.permission):            
            if not request.user.has_perm(self.permission):
                response['type'] = 'result'
                response['data'] = 'You need `%s` permission to run this method' % self.permission
                response['name'] = self.event
                return HttpResponse(simplejson.dumps(response, cls=DjangoJSONEncoder), mimetype='application/json')
        
        try:
            if self.func:
                response['data'] = self.func(request)
                response['name'] = self.event
                response['type'] = 'event'                
            else:
                raise RuntimeError("The server provider didn't register a function to run yet")
                
        except Exception, e:            
            if settings.DEBUG:
                etype, evalue, etb = sys.exc_info()
                response['type'] = 'exception'                
                response['message'] = traceback.format_exception_only(etype, evalue)[0]
                response['where'] = traceback.extract_tb(etb)[-1]
            else:
                raise e
        
        return HttpResponse(simplejson.dumps(response, cls=DjangoJSONEncoder), mimetype='application/json')
