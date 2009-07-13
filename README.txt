Introduction
============

This package provides a simple way to expose functions/views in django to the `Ext.Direct`_ package
included in `ExtJS 3.0`_ following the `Ext.Direct specification`_

.. _`ExtJS 3.0`: http://www.extjs.com/
.. _`Ext.Direct`: http://extjs.com/blog/2009/05/13/introducing-ext-direct/
.. _`Ext.Direct specification`: http://extjs.com/products/extjs/direct.php
  

Take a look to tests.py and test_urls.py to see the needed setup.

First, let's create a test browser::

  >>> from django.test.client import Client
  >>> client = Client()

Now, we should be able to get the `provider.js` that will register
our ExtDirect provider. As we didn't register any function yet, the `actions` for this provider will
be an empty config object ::
  
  >>> response = client.get('/remoting/provider.js/')
  >>> print response.content #doctest: +NORMALIZE_WHITESPACE  
  Ext.onReady(function() {
      Ext.Direct.addProvider({"url": "/remoting/router/",
                              "type": "remoting",
                              "namespace": "django",
                              "actions": {}});
  });
  
So, all you have to do to register the Ext.DirectProvider in your web application is::

  <script src="/remoting/script.js/"></script>
  
We will use the `_config` property from now on, (the config object passed to addProvider function)::
  
  >>> from pprint import pprint
  >>> from extdirect.django import remoting
  >>> from extdirect.django import tests
  
  >>> pprint(tests.remote_provider._config)
  {'actions': {},
   'namespace': 'django',
   'type': 'remoting',
   'url': '/remoting/router/'}
   
Ok, now we are going to register a new function on our provider instance (tests.remote_provider)

  >>> @remoting('user', tests.remote_provider)
  ... def list(request):
  ...   pass
  ...

By default, `formHandler` will be set to false, `len` to 0 and `name` to the function name.

  >>> pprint(tests.remote_provider._config)
  {'actions': {'user': [{'formHandler': False, 'len': 0, 'name': 'list'}]},
   'namespace': 'django',
   'type': 'remoting',
   'url': '/remoting/router/'}

Note that ExtDirect has `actions` (controllers) and `methods`. But here, we have just functions.
So, we use::

  @remoting('user', tests.remote_provider)
  def list(request):
  
to say, "add the `list` function to the `user` action".

It's importat to note, that the signature that you pass to `@remoting` it's not relevant in the server-side.
The functions that we expose to Ext.Direct should receive just the `request` instace like any other django view.
When the function it's a form handler (form_handler=True), all the parameters will be present in
`request.POST`. Otherwise, the parameters will be available in `request.extdirect_post_data`.

Let's register a few more functions

  >>> @remoting('user', tests.remote_provider, form_handler=True)
  ... def update(request):  
  ...   return dict(success=True, data=[request.POST['username'], request.POST['password']])
  ...
  >>> @remoting('posts', tests.remote_provider, len=1)
  ... def all(request):
  ...   #just return the recieved data
  ...   return dict(success=True, data=request.extdirect_post_data)
  ...
  
Let's take a look to the config object for our provider::
  
  >>> pprint(tests.remote_provider._config)
  {'actions': {'posts': [{'formHandler': False, 'len': 1, 'name': 'all'}],
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
  
  >>> pprint(simplejson.loads(response.content))
  {u'action': u'posts',
   u'isForm': False,
   u'method': u'all',
   u'result': {u'data': [{u'tag': u'extjs'}], u'success': True},
   u'tid': 1,
   u'type': u'rpc'}
   
Let's try with a formHandler, you may want to see the `Ext.Direct Form Integration`_ for a live example.

.. _`Ext.Direct Form Integration`: http://extjs.com/deploy/dev/examples/direct/direct-form.php

When we run::

  panelForm.getForm().submit()
  
Ext.Direct will make a POST request like this::

  >>> response = client.post('/remoting/router/',
  ...                       {'username': 'sancho',
  ...                        'password': 'sancho',
  ...                        'extAction': 'user',
  ...                        'extMethod': 'update',
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
