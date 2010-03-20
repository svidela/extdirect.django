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


#We use this model to test the metadata generator module
class MetaModel(models.Model):
    
    name = models.TextField(verbose_name="name", max_length=35)
    
    nickname = models.TextField(verbose_name="nickname", max_length=35, blank=True, default="nick")
    
    age = models.IntegerField(verbose_name="age")
    
    creation_date = models.DateField(verbose_name="Creation")

    
    fk_model = models.ForeignKey(FKModel, verbose_name="fk")

class HandField(models.Field):

    description = "A hand of cards (bridge style)"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 104
        super(HandField, self).__init__(*args, **kwargs)
        
class MetaModelCustomField(models.Model):
    
    hand = HandField()
    
#Auth tests
class PermModel(models.Model):
    class Meta:
        permissions = (
            ("my_permission", "My Permission"),
        )
