from django.conf.urls.defaults import *
import tests

urlpatterns = patterns(
    '',
    (r'^remoting/router/$', tests.remote_provider.router),
    (r'^remoting/provider.js/$', tests.remote_provider.script)
)

