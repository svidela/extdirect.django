Introduction
============

This package provides a simple way to expose functions/views in django to the
`Ext.Direct`_ package included in `ExtJS 3.0`_ following the `Ext.Direct specification`_

.. _`ExtJS 3.0`: http://www.extjs.com/
.. _`Ext.Direct`: http://extjs.com/blog/2009/05/13/introducing-ext-direct/
.. _`Ext.Direct specification`: http://extjs.com/products/extjs/direct.php
  

Take a look to docs/INSTALL.txt, tests.py and test_urls.py to see the needed setup.

We need to set the __name__ variable to access to function.__module__ later::

  >>> __name__ = 'extdirect.django.doctest'

Let's create a test browser::

  >>> from django.test.client import Client
  >>> client = Client()

Register the ExtDirect remoting provider
----------------------------------------

Now, we should be able to get the `provider.js` that will register
our ExtDirect provider. As we didn't register any function yet, the `actions`
for this provider will be an empty config object ::
  
  >>> response = client.get('/remoting/provider.js/')
  >>> print response.content #doctest: +NORMALIZE_WHITESPACE  
  Ext.onReady(function() {
      Ext.Direct.addProvider({"url": "/remoting/router/",
                              "type": "remoting",
                              "namespace": "django",
                              "actions": {}});
  });
  
So, all you have to do to register the Ext.RemotingProvider in your web application is::

  <script src="/remoting/provider.js/"></script>
  
Direct access to the descriptor API
-----------------------------------

You may want to access to the whole descriptor API of your ExtDirect Remoting
provider. In that case, we could make a request as follows::

  >>> response = client.get('/remoting/api/')
  >>> print response.content #doctest: +NORMALIZE_WHITESPACE
  Ext.ns('django');
  django.Descriptor = {"url": "/remoting/router/",
                       "type": "remoting",
                       "namespace": "django",
                       "actions": {}}

Note that this response it's javascript code::

  >>> print response.__getitem__('content-type')
  text/javascript
  
But according to the Ext.Direct specification, we should also
be able to get the descriptor API as a JSON packet::

  >>> response = client.get('/remoting/api/', {'format': 'json'})
  >>> print response.content #doctest: +NORMALIZE_WHITESPACE
  {"url": "/remoting/router/",
   "type": "remoting",
   "namespace": "django",
   "actions": {},
   "descriptor": "django.Descriptor"}
   
And just to be sure::

  >>> print response.__getitem__('content-type')
  application/json
  
Using Ext.direct.RemotingProvider
---------------------------------
  
We will use the `_config` property from now on, (the config object passed to
`addProvider` function)::
  
  >>> from pprint import pprint
  >>> from extdirect.django import remoting
  >>> from extdirect.django import tests
  
  >>> pprint(tests.remote_provider._config)
  {'actions': {},
   'namespace': 'django',
   'type': 'remoting',
   'url': '/remoting/router/'}
   
Ok, now we are going to register a new function on our provider instance (`tests.remote_provider`)::

  >>> @remoting(tests.remote_provider, action='user')
  ... def list(request):
  ...   pass
  ...

By default, `formHandler` will be set to false, `len` to 0 and `name` to the function name::

  >>> pprint(tests.remote_provider._config)
  {'actions': {'user': [{'formHandler': False, 'len': 0, 'name': 'list'}]},
   'namespace': 'django',
   'type': 'remoting',
   'url': '/remoting/router/'}

Note that ExtDirect has `actions` (controllers) and `methods`. But here, we have just functions.
So, we use::

  @remoting(tests.remote_provider, action='user')
  def list(request):
  
to say, "add the `list` function to the `user` action".
But this is optional, if we don't set the `action`, the default value it's the function __module__
attribute (replacing '.' with '_')

It's important to note, that the signature that you pass to `@remoting` it's not
relevant in the server-side. The functions that we expose to Ext.Direct should
receive just the `request` instace like any other django view. The parameters for
the exposed function, will be available in `request.extdirect_post_data` (when
the function it's a form handler (form_handler=True), all the parameters will be
also available in `request.POST`).

Let's register a few more functions::

  >>> @remoting(tests.remote_provider, action='user', form_handler=True)
  ... def update(request):  
  ...   return dict(success=True, data=[request.POST['username'], request.POST['password']])
  ...
  >>> @remoting(tests.remote_provider, action='posts', len=1)
  ... def all(request):
  ...   #just return the recieved data
  ...   return dict(success=True, data=request.extdirect_post_data)
  ...
  >>> @remoting(tests.remote_provider)
  ... def module_action(request):  
  ...   return dict(success=True)  
  
Let's take a look to the config object for our provider::
  
  >>> pprint(tests.remote_provider._config) #doctest: +NORMALIZE_WHITESPACE
  {'actions': {'extdirect_django_doctest': [{'formHandler': False, 'len': 0, 'name': 'module_action'}],
               'posts': [{'formHandler': False, 'len': 1, 'name': 'all'}],
               'user': [{'formHandler': False, 'len': 0, 'name': 'list'},
                        {'formHandler': True, 'len': 0, 'name': 'update'}]},
   'namespace': 'django',
   'type': 'remoting',
   'url': '/remoting/router/'}

It's time to make an ExtDirect call. In our javascript we will write just::

  django.posts.all({tag: 'extjs'})
  
This will be converted to a POST request::

  >>> from django.utils import simplejson
  >>> rpc = simplejson.dumps({'action': 'posts',
  ...                         'tid': 1,
  ...                         'method': 'all',
  ...                         'data':[{'tag': 'extjs'}],
  ...                         'type':'rpc'})
  >>> response = client.post('/remoting/router/', rpc, 'application/json')

And let's check the reponse::
  
  >>> pprint(simplejson.loads(response.content)) #doctest: +NORMALIZE_WHITESPACE
  {u'action': u'posts',
   u'method': u'all',
   u'result': {u'data': [{u'tag': u'extjs'}], u'success': True},
   u'tid': 1,
   u'type': u'rpc'}
   
Let's try with a formHandler, you may want to see the `Ext.Direct Form Integration`_
for a live example.

.. _`Ext.Direct Form Integration`: http://extjs.com/deploy/dev/examples/direct/direct-form.php

When we run::

  panelForm.getForm().submit()
  
Ext.Direct will make a POST request like this::

  >>> response = client.post('/remoting/router/',
  ...                       {'username': 'sancho',
  ...                        'password': 'sancho',
  ...                        'extAction': 'user',
  ...                        'extMethod': 'update',
  ...                        'extUpload': False,
  ...                        'extTID': 2,
  ...                        'extType': 'rpc'})

Let's check the reponse::

  >>> pprint(simplejson.loads(response.content))
  {u'action': u'user',
   u'isForm': True,
   u'method': u'update',
   u'result': {u'data': [u'sancho', u'sancho'], u'success': True},
   u'tid': u'2',
   u'type': u'rpc'}
   
If you use `fileUpload`_ in your ExtJS form, the files will be available in
`request.FILES`, just as Django handles the `File Uploads`_.

.. _`fileUpload`: http://www.extjs.com/deploy/dev/docs/?class=Ext.form.BasicForm#Ext.form.BasicForm-fileUpload
.. _`File Uploads`: http://docs.djangoproject.com/en/dev/topics/http/file-uploads/

Now, we are going to see what happen with exceptions. Following the Ext.Direct specification
extdirect.django will check if django it's running on debug mode (settings.DEBUG=True) and in
that case, it will return the exception to the browser. Otherwise, the exceptions must be
catched by the function that you expose.

First, let's expose a function that raise an Exception::

  >>> @remoting(tests.remote_provider, action='errors')
  ... def error(request):  
  ...   return "A common mistake" + 1
  
And now, we simulate the execution on debug mode::

  >>> from django.conf import settings
  >>> settings.DEBUG = True

  >>> rpc = simplejson.dumps({'action': 'errors',
  ...                         'tid': 1,
  ...                         'method': 'error',
  ...                         'data':[],
  ...                         'type':'rpc'})
  >>> response = client.post('/remoting/router/', rpc, 'application/json')
  >>> pprint(simplejson.loads(response.content))
  {u'action': u'errors',
   u'message': u"TypeError: cannot concatenate 'str' and 'int' objects\n",
   u'method': u'error',
   u'tid': 1,
   u'type': u'exception',
   u'where': [u'<doctest ...>',
              3,
              u'error',
              u'return "A common mistake" + 1']}

Note that in the `where` attribute, you will have [filename, lineno, function, statment] in order to
help you at debugging time.

Let's see what happen if we turn off the debug mode::

  >>> settings.DEBUG = False
  >>> response = client.post('/remoting/router/', rpc, 'application/json') #doctest: +NORMALIZE_WHITESPACE  
  Traceback (most recent call last):
  ...
  TypeError: cannot concatenate 'str' and 'int' objects  
  
The exception raised must be catched in the server and the browser doesn't know anything about it.

Register the ExtDirect polling provider
---------------------------------------

As we did above with the ExtDirect Remoting provider::

  >>> response = client.get('/polling/provider.js/')
  >>> print response.content #doctest: +NORMALIZE_WHITESPACE
  Ext.onReady(function() {
      Ext.Direct.addProvider({"url": "/polling/router/", "type": "polling"});
  });
  
So, all you have to do to register the Ext.PollingProvider in your web application is::

  <script src="/polling/provider.js/"></script>

Using Ext.direct.PollingProvider
--------------------------------

In this section we are going to show how you can use the Ext.direct.PollingProvider.
Ext.direct.PollingProvider, provides for repetitive polling of the server at
distinct intervals (defaults to 3000 - every 3 seconds).

As we didn't set a function to our polling provider, if call it we should get an exception::

  >>> response = client.get('/polling/router/') #doctest: +NORMALIZE_WHITESPACE
  Traceback (most recent call last):
  ...
  RuntimeError: The server provider didn't register a function to run yet

But, as with ExtRemotingProvider, when Django it's in debug mode, the exception it's
returned to the browser::

  >>> settings.DEBUG = True
  >>> response = client.get('/polling/router/') 
  >>> pprint(simplejson.loads(response.content)) #doctest: +NORMALIZE_WHITESPACE
  {u'message': u"RuntimeError: The server provider didn't register a function to run yet\n",
   u'type': u'exception',
   u'where': [u'...',
              311,
              u'router',
              u'raise RuntimeError("The server provider didn\'t register a function to run yet")']}

  >>> settings.DEBUG = False
  
So, let's declare a simple function an assign it to our polling provider::

  >>> from extdirect.django import polling
  >>> @polling(tests.polling_provider)
  ... def my_polling(request):
  ...   return "I'm tired..."

  >>> response = client.get('/polling/router/') 
  >>> pprint(simplejson.loads(response.content)) #doctest: +NORMALIZE_WHITESPACE
  {u'data': u"I'm tired...", u'name': u'some-event', u'type': u'event'}


Using the ExtDirectStore helper class
-------------------------------------

ExtDirectStore it's a helper class that you may want to use to load a given
Ext.data.DirectStore in ExtJS.

It's important to note that you should use len=1 (python) and paramsAsHash=true (javascript) in
order to get everything working

Let's see the simplest use case::

  >>> from extdirect.django import ExtDirectStore
  >>> from extdirect.django.models import ExtDirectStoreModel
  >>> list = ExtDirectStore(ExtDirectStoreModel)
  >>> pprint(list.query()) #doctest: +NORMALIZE_WHITESPACE
  {'records': [{'id': 1, 'name': u'Homer'}, {'id': 2, 'name': u'Joe'}], 'total': 2}
  
So a quick and almost complete example could be:

In django::

  @remoting(provider, action='user', len=1)
  def load_users(request):
      data = request.extdirect_post_data[0]
      users = ExtDirectStore(User)
      return users.query(**data)

In ExtJS::

  new Ext.data.DirectStore({
        paramsAsHash: true, 
        directFn: django.user.load_users,        
        fields: [
            {name: 'first_name'}, 
            {name: 'last_name'}, 
            {name: 'id'}
        ],
        // defaults in django
        root: 'records',
        idProperty: 'id',
        totalProperty: 'total',
        ...
  })    
  
As we saw in the example above, you may want to pass a keyword arguments to the
method `query` in order to filter your query::

  >>> pprint(list.query(id=1))
  {'records': [{'id': 1, 'name': u'Homer'}], 'total': 1}
  
You are able to change (or set at creation time) the keywords used by ExtDirectStore::

  >>> list.root = 'users'
  >>> list.total = 'result'
  >>> pprint(list.query())
  {'result': 2, 'users': [{'id': 1, 'name': u'Homer'}, {'id': 2, 'name': u'Joe'}]}
  
If you are using Paging, ExtDirectStore will take care::

  >>> pprint(list.query(start=0, limit=2))
  {'result': 2, 'users': [{'id': 1, 'name': u'Homer'}, {'id': 2, 'name': u'Joe'}]}

  >>> pprint(list.query(start=0, limit=1))
  {'result': 2, 'users': [{'id': 1, 'name': u'Homer'}]}

  >>> pprint(list.query(start=1, limit=1))
  {'result': 2, 'users': [{'id': 2, 'name': u'Joe'}]}
  
Again, you are free to change the keywords `start` and `limit` to whatever you want to::

  >>> list.start = 'from'
  >>> list.limit = 'to'
  >>> kw = {'from':0, 'to':1}
  >>> pprint(list.query(**kw))
  {'result': 2, 'users': [{'id': 1, 'name': u'Homer'}]}
  
Sorting it's also included::

  >>> pprint(list.query(sort='name', dir='ASC'))
  {'result': 2, 'users': [{'id': 1, 'name': u'Homer'}, {'id': 2, 'name': u'Joe'}]}

  >>> pprint(list.query(sort='name', dir='DESC'))
  {'result': 2, 'users': [{'id': 2, 'name': u'Joe'}, {'id': 1, 'name': u'Homer'}]}
  
And guess what...? You are able to change this keywords too::

  >>> list.sort = 'sort_field'
  >>> list.dir = 'sort_order'
  
  >>> pprint(list.query(sort_field='name', sort_order='ASC'))
  {'result': 2, 'users': [{'id': 1, 'name': u'Homer'}, {'id': 2, 'name': u'Joe'}]}

  >>> pprint(list.query(sort_field='name', sort_order='DESC'))
  {'result': 2, 'users': [{'id': 2, 'name': u'Joe'}, {'id': 1, 'name': u'Homer'}]}
  
Finally, sometimes you will need to run complex queries. We have two options for that.
First, you could pass or set, an `extras` parameter to the ExtDirectStore. This should be a list of
tuples like::

  >>> def name_size(rec):
  ...    return len(rec.name)
  >>>
  >>> extras = [('name_size', name_size),('name_upper', lambda rec: rec.name.upper())]
  >>> list.extras = extras
  >>> pprint(list.query()) #doctest: +NORMALIZE_WHITESPACE
  {'result': 2,
   'users': [{'id': 1,
              'name': u'Homer',
              'name_size': 5,
              'name_upper': u'HOMER'},
             {'id': 2,
              'name': u'Joe',
              'name_size': 3,
              'name_upper': u'JOE'}]}
              
  >>> list.extras = []

Each item in the `extras` list should be a tuple with:
 - attribute name
 - callable object (taking only one required parameter)

The callable object in each tuple, will be executed for each object in the queryset
to get the value for that attribute.

The second option to run complex queries it's very simple.::

  >>> qs = ExtDirectStoreModel.objects.exclude(id=2)
  >>> pprint(list.query(qs))
  {'result': 1, 'users': [{'id': 1, 'name': u'Homer'}]}
  
Here, we just need to pass a valid queryset to the `query` function. Using this
queryset, ExtDirectStore, will apply everything that we already saw
(filter, paging, sorting). You are able to create a complex queryset using
all of the Django ORM features and then pass it to the method `query`.

Finally, let's see what happen when you define ForeignKey in your models::

  >>> from extdirect.django.models import Model
  >>> ds = ExtDirectStore(Model)
  >>> pprint(ds.query())
  {'records': [{'fk_model': 1, 'fk_model_id': 1, 'id': 1}], 'total': 1}
  
For each, foreign key field (`fk_model`), you will get two attributes with the same value:
 - fk_model
 - fk_model_id
