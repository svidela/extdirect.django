# This is required for:
# $> ./django test
# to run the extdirect.django tests (remember to include extdirect.django in the INSTALLED_APPS).

# see: http://code.djangoproject.com/ticket/7198
# Thanks to http://pypi.python.org/pypi/rpc4django/

from django.db import models

class FKModel(models.Model):
    attr = models.CharField(verbose_name="attribute", max_length=35)
    
class Model(models.Model):
    fk_model = models.ForeignKey(FKModel, verbose_name="fk")

class ExtDirectStoreModel(models.Model):
    #We use this class only for testing purpose
    name = models.CharField(verbose_name="name", max_length=35)
    
