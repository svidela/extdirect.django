from extdirect.django.store import ExtDirectStore

from django.db import transaction
from django.core.serializers import serialize
from django.utils.encoding import force_unicode
from django.views.generic.create_update import get_model_and_form_class

def format_form_errors(errors):
    """
    Convert the ErrorDict and ErrorList Django objects
    to dict and list standard python objects.
    Otherwise we can't serialize them to JSON.
    """
    err = {}
    for k, v in errors.items():
        err[k] = [force_unicode(e) for e in v]
        
    return err

class BaseExtDirectCRUD(object):
    """
    Base class for CRUD actions.
    
    Implements all the methods that you may want to
    re-implement in your own class.
    """
    model = None
    form = None
    
    #Defaults
    isForm = False
    parse_fk_fields = True
    show_form_validation = False 
    metadata = True   
    
    #Messages
    create_success_msg = "Records created"
    create_failure_msg = "There was an error while trying to save some of the records"
    
    update_success_msg = "Records updated"
    update_failure_msg = "There was an error while trying to save some of the records"
    
    destroy_success_msg = "Objects deleted"
    
    #Seems that Ext.form.action.DirectLoad always look for this metadata.
    #If you find a way to change that on the client-side, please let me know.
    direct_load_metadata = {'root': 'data', 'total' : 'total', 'success': 'success'}
    
    def __init__(self, provider, action, login_required, permission):                
        self.store = self.direct_store()
        
        #same as Django generic views
        self.model, self.form = get_model_and_form_class(self.model, self.form)
        
        #Register the CRUD actions. You may want to re-implement these methods
        #in your class definition in order to change the defaults registrations.
        self.reg_create(provider, action, login_required, permission)
        self.reg_read(provider, action, login_required, permission)
        self.reg_load(provider, action, login_required, permission)
        self.reg_update(provider, action, login_required, permission)
        self.reg_destroy(provider, action, login_required, permission)
            
    def reg_create(self, provider, action, login_required, permission):
        provider.register(self.create, action, 'create', 1, self.isForm, login_required, permission)
        
    def reg_read(self, provider, action, login_required, permission):        
        provider.register(self.read, action, 'read', 1, False, login_required, permission)
        
    def reg_load(self, provider, action, login_required, permission):        
        provider.register(self.load, action, 'load', 1, False, login_required, permission)        
        
    def reg_update(self, provider, action, login_required, permission):
        provider.register(self.update, action, 'update', 1, self.isForm, login_required, permission)

    def reg_destroy(self, provider, action, login_required, permission):
        provider.register(self.destroy, action, 'destroy', 1, False, login_required, permission)
    
    def direct_store(self):
        return ExtDirectStore(self.model, metadata=self.metadata)
        
    def query(self, **kw):
        #It must return `None` or a valid Django Queryset
        return None
    
    #All the "extract_(action)_data" will depend on how you registered each method.
    def extract_create_data(self, request, sid):
        #It must return a dict object or a list of dicts with the values ready
        #to create the new instance or instances.
        if self.isForm:
            return dict(request.extdirect_post_data.items())
        else:
            return request.extdirect_post_data[0][self.store.root]
    
    def extract_read_data(self, request):
        #It must return a dict object ready to be passed
        #to the query method of ExtDirectStore class.
        return request.extdirect_post_data[0]
        
    def extract_load_data(self, request):
        #It must return a dict object ready to be passed
        #to the query method of ExtDirectStore class.
        return request.extdirect_post_data[0]        
    
    def extract_update_data(self, request, sid):
        #It must return a dict object or a list of dicts with the values ready
        #to update the instance or instances.
        if self.isForm:
            return dict(request.extdirect_post_data.items())        
        else:
            return request.extdirect_post_data[0][self.store.root]
    
    def extract_destroy_data(self, request):
        #It must return the id or list of id's to be deleted.
        return request.extdirect_post_data[0][self.store.root]
    
    def _single_create(self, data, files=None):
        #id='ext-record-#'
        data.pop("id", "")
    
        c = None
        if self.parse_fk_fields:
            data = self._fk_fields_parser(data)
                     
        form = self.form(data, files)
        if form.is_valid():
            c = form.save()                
            self.post_single_create(c)
            return c.id, ""
        else:
            return 0, form.errors            
           
    def _single_update(self, data, files=None):
        id = data.pop("id")        
        obj = self.model.objects.get(pk=id)        
        
        if self.parse_fk_fields:
            data = self._fk_fields_parser(data)
                            
        form = self.form(data, files, instance=obj)
        if form.is_valid():
            obj = form.save()        
            self.post_single_update(obj)
            return obj.id, ""
        else:
            return 0, form.errors
        
    # Process of data in order to fix the foreign keys according to how
    # the `extdirect` serializer handles them.
    # {'fk_model': 'FKModel','fk_model_id':1} --> {'fk_model':1, 'fk_model_id': 1}
    def _fk_fields_parser(self, data):
        for field in data.keys():
            if field[-3:] == '_id': #and isinstance(data[field], int) and not isinstance(data[field[:-3]], int):
                data[field[:-3]] = data[field]
                data.pop(field)
        return data        

    #Very simple hooks that you may want to use
    #to do something.
    def pre_create(self, data):
        return True, ""
        
    def post_create(self, ids):
        pass
    
    def post_single_create(self, obj):
        pass

    def pre_read(self, data):
        return True, ""
        
    def pre_load(self, data):
        return True, ""        

    def pre_update(self, data):
        return True, ""
        
    def post_update(self, ids):
        pass
    
    def post_single_update(self, obj):
        pass

    def pre_destroy(self, data):
        return True, ""
        
    def post_destroy(self, id):
        pass
    
    def failure(self, msg):
        return {self.store.success: False, self.store.root: [], self.store.total: 0, self.store.message: msg}
            
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
        errors = {}
        if isinstance(extdirect_data, list):
            for data in extdirect_data:
                id, errors = self._single_create(data, request.FILES)
                if id:
                    ids.append(id)
                else:            
                    success = False
                    break
        else:
            id, errors = self._single_create(extdirect_data, request.FILES)            
            if id:
                ids.append(id)
            else:
                success = False
            
        if success:
            transaction.commit()    
            self.post_create(ids)
            res = self.store.query(self.model.objects.filter(pk__in=ids), metadata=False)            
            res[self.store.message] = self.create_success_msg
            return res
        else:
            transaction.savepoint_rollback(sid)
            if self.show_form_validation:
                err = format_form_errors(errors)                
            else:
                err = self.create_failure_msg
                
            return self.failure(err)
        
    #READ        
    def read(self, request):
        extdirect_data = self.extract_read_data(request)
        ok, msg = self.pre_read(extdirect_data)        
        if ok:           
            return self.store.query(qs=self.query(**extdirect_data), **extdirect_data)
        else:
            return self.failure(msg)
            
    #LOAD            
    def load(self, request):
        #Almost the same as 'read' action but here we call
        #the serializer directly with a fixed metadata (different
        #from the self.store). Besides, we assume that the load
        #action should return a single record, so all the query
        #options are not needed.
        meta = self.direct_load_metadata
        extdirect_data = self.extract_load_data(request)
        ok, msg = self.pre_load(extdirect_data)         
        if ok:                  
            queryset = self.model.objects.filter(**extdirect_data)
            res = serialize('extdirect', queryset, meta=meta, single_cast=True)
            return res
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
        errors = {}
        if isinstance(records, list):
            #batch update
            for data in records:
                id, errors = self._single_update(data, request.FILES)
                if id:
                    ids.append(id)
                else:
                    success = False
                    break

        else:
            #single update
            id, errors = self._single_update(records, request.FILES)
            if id:
                ids.append(id)
            else:
                success = False

        if success:
            transaction.commit()    
            self.post_update(ids)
            res = self.store.query(self.model.objects.filter(pk__in=ids), metadata=False)
            res[self.store.message] = self.update_success_msg
            return res
        else:
            transaction.savepoint_rollback(sid)
            if self.show_form_validation:
                err = format_form_errors(errors)                
            else:
                err = self.update_failure_msg
                
            return self.failure(err)
    
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
        
        return {self.store.success: True,
                self.store.message: self.destroy_success_msg,
                self.store.root: []}
    
