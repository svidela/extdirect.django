from extdirect.django.store import ExtDirectStore
from django.forms.models import modelform_factory
from django.db import transaction
from django.core.serializers import serialize
from django.shortcuts import get_object_or_404, render_to_response

from django.utils import simplejson

ACTIONS = ('CREATE', 'READ', 'UPDATE', 'DESTROY')

class BaseExtDirectCRUD(object):
    """
    Base class for CRUD actions.
    
    Implements all the methods that you may want to
    re-implement in your own class.
    """
    model = None
    form = None    
    
    def __init__(self, provider, action, login_required, permission):
        self.store = self.direct_store()
        
        if not self.form:
            self.form = modelform_factory(self.model)
        
        #Register the CRUD actions. You may want to re-implement these methods
        #in your class definition in order to change the defaults registrations.
        self.reg_create(provider, action, login_required, permission)
        self.reg_read(provider, action, login_required, permission)
        self.reg_update(provider, action, login_required, permission)
        self.reg_destroy(provider, action, login_required, permission)
            
    def reg_create(self, provider, action, login_required, permission):
        provider.register(self.create, action, 'create', 1, False, login_required, permission)
        
    def reg_read(self, provider, action, login_required, permission):        
        provider.register(self.read, action, 'read', 1, False, login_required, permission)
        
    def reg_update(self, provider, action, login_required, permission):
        provider.register(self.update, action, 'update', 2, False, login_required, permission)

    def reg_destroy(self, provider, action, login_required, permission):
        provider.register(self.destroy, action, 'destroy', 1, False, login_required, permission)
    
    def direct_store(self):
        return ExtDirectStore(self.model, metadata=True)
    
    #All the "extract_(action)_data" will depend on how you registered each method.
    def extract_create_data(self, request, sid):
        #It must return a dict object or a list of dicts with the values ready
        #to create the new instance or instances.
        return request.extdirect_post_data[0]
    
    def extract_read_data(self, request):
        #It must return a dict object ready to be passed
        #to the query method of ExtDirectStore class.
        return request.extdirect_post_data[0]
    
    def extract_update_data(self, request, sid):
        #It must return a dict object or a list of dicts with the values ready
        #to update the instance or instances.
        return request.extdirect_post_data[1]
    
    def extract_destroy_data(self, request):
        #It must return the id or list of id's to be deleted.
        return request.extdirect_post_data[0]
    
    def pre_create(self, data):
        return True, ""
        
    def post_create(self, ids):
        pass
    
    def post_single_create(self, obj):
        pass

    def _single_create(self, data):
        #id='ext-record-#'
        data.pop("id", "")
    
        c = None
        form = self.form(data=data)
        if form.is_valid():
            c = form.save()                
            self.post_single_create(c)
            return c.id        
        else:
            return 0
        
    def pre_read(self, data):
        return True, ""

    def pre_update(self, data):
        return True, ""
        
    def post_update(self, ids):
        pass
    
    def post_single_update(self, obj):
        pass
    
    def _single_update(self, data):
        data = dict(data.items())        
        id = data.pop("id")        
        obj = self.model.objects.get(pk=id)        
    
        all_fields = serialize('python', [obj])[0]['fields']
        all_fields.update(data)

        form = self.form(all_fields, instance=obj)
        if form.is_valid():
            obj = form.save()        
            self.post_single_update(obj)
            return obj.id
        else:
            return 0

    def pre_destroy(self, data):
        return True, ""
        
    def post_destroy(self, id):
        pass
    
    def failure(self, msg):
        return {self.store.success: False, self.store.root: [], self.store.total: 0, 'message': msg}
            
class ExtDirectCRUD(BaseExtDirectCRUD):
    """
    ExtDirectCRUD main class.
    
    Implements the main CRUD actions.
    
    You shouldn't re-implement these methods, see 
    BaseExtDirectCRUD if you need custom behavior.
    """
    
    #CREATE            
    @transaction.commit_manually
    def create(self, request):
        sid = transaction.savepoint()
        
        extdirect_data = self.extract_create_data(request, sid)        
        
        ok, msg = self.pre_create(extdirect_data)
        if not ok:
            return self.failure(msg)
                    
        ids = []
        success = True
        
        if isinstance(extdirect_data, list):
            for data in extdirect_data:
                id = self._single_create(data)
                if id:
                    ids.append(id)
                else:            
                    success = False
                    break
        else:
            id = self._single_create(extdirect_data)
            if id:
                ids.append(id)
            else:
                success = False
            
        if success:
            transaction.commit()    
            self.post_create(ids)
            res = self.store.query(self.model.objects.filter(pk__in=ids), metadata=False)            
            res['message'] = 'Records created'
            return res
        else:
            transaction.savepoint_rollback(sid)
            return self.failure("There was an error while trying to save some of the records.")
        
    #READ        
    def read(self, request):
        extdirect_data = self.extract_read_data(request)
        ok, msg = self.pre_read(extdirect_data)        
        if ok:           
            return self.store.query(**extdirect_data)
        else:
            return self.failure(msg)
    
    #UPDATE    
    @transaction.commit_manually
    def update(self, request):
        sid = transaction.savepoint()        

        extdirect_data = self.extract_update_data(request, sid)
        
        ok, msg = self.pre_update(extdirect_data)
        if not ok:
            return self.failure(msg)
        
        ids = []
        success = True
        records = extdirect_data                
        
        if isinstance(records, list):
            #batch update
            for data in records:
                id = self._single_update(data)
                if id:
                    ids.append(id)
                else:
                    success = False
                    break

        else:
            #single update
            id = self._single_update(records)
            if id:
                ids.append(id)
            else:
                success = False

        if success:
            transaction.commit()    
            self.post_update(ids)
            res = self.store.query(self.model.objects.filter(pk__in=ids), metadata=False)
            res['message'] = "Records updated"
            return res
        else:
            transaction.savepoint_rollback(sid)
            return self.failure("There was an error while trying to save some of the records.")
    
    #DESTROY        
    def destroy(self, request):
        ids = self.extract_destroy_data(request)
        
        ok, msg = self.pre_destroy(ids)
        if not ok:
            return self.failure(msg)
        
        if isinstance(ids, list):
            cs = self.model.objects.filter(pk__in=ids)
        else:            
            cs = [self.model.objects.get(pk=ids)]
        
        for c in cs:
            i = c.id
            c.delete()        
            self.post_destroy(i)
        
        return {self.store.success:True, 'message':"Objects deleted"}
    
