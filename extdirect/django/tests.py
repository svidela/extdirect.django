import doctest
import unittest

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
    optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    globs = {}
    
    suite = unittest.TestSuite()

    suite.addTest(doctest.DocFileSuite(
        '../../README.txt',
        optionflags=optionflags,
        setUp=setUp,
        tearDown=tearDown,
        globs=globs))
    
    return suite

