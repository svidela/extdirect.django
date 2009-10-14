from django.conf.urls.defaults import *
import tests

urlpatterns = patterns(
    '',
    (r'^remoting/router/$', tests.remote_provider.router),
    (r'^remoting/provider.js/$', tests.remote_provider.script),
    (r'^remoting/api/$', tests.remote_provider.api),
    (r'^polling/router/$', tests.polling_provider.router),
    (r'^polling/provider.js/$', tests.polling_provider.script)
)

