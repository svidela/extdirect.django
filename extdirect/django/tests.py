import doctest

from extdirect.django import ExtRemotingProvider  
remote_provider = ExtRemotingProvider(namespace='django', url='/remoting/router/')

from django.conf import settings
from django.core.urlresolvers import clear_url_caches

def setUp(self):    
    self._old_root_urlconf = settings.ROOT_URLCONF
    settings.ROOT_URLCONF = 'extdirect.django.test_urls'
    clear_url_caches()

def tearDown(self):                
    settings.ROOT_URLCONF = self._old_root_urlconf
    clear_url_caches()            

def suite():
    return doctest.DocFileSuite('../../README.txt',
                                setUp=setUp,
                                tearDown=tearDown)    

