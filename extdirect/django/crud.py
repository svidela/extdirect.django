from extdirect.django.store import ExtDirectStore
from django.forms.models import modelform_factory
from django.db import transaction
from django.core.serializers import serialize

ACTIONS = ('CREATE', 'READ', 'UPDATE', 'DESTROY')

class BaseExtDirectCRUD(object):
    """
    Base class for CRUD actions.
    
    Implements all the methods that you may want to
    re-implement in your own class.
    """
    model = None
    form = None    
    
    def __init__(self):
        self.store = self.direct_store()
        
        if not self.form:
            self.form = modelform_factory(self.model)
    
    def direct_store(self):
        return ExtDirectStore(self.model)
    
    def extract_data(self, request, action):
        if action not in ACTIONS:
            raise AttributeError, "action must be one of: %s" % str(ACTIONS)
        
        if action in ('CREATE', 'READ', 'DESTROY'):
            return request.extdirect_post_data[0]
        
        else:
            return request.extdirect_post_data
    
    def pre_create(self, data):
        return True, ""
        
    def post_create(self, ids):
        pass
    
    def post_single_create(self, obj):
        pass

    def _single_create(self, data):
        #id='ext-record-#'
        data.pop("id")        
            
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
        extdirect_data = self.extract_data(request, 'CREATE')
        
        ok, msg = self.pre_create(extdirect_data)
        if not ok:
            return self.failure(msg)
                    
        ids = []
        success = True
        sid = transaction.savepoint()
        
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
            res = self.store.query(self.model.objects.filter(pk__in=ids))            
            res['message'] = 'Records created'
            return res
        else:
            transaction.savepoint_rollback(sid)
            return self.failure("There was an error while trying to save some of the records.")
        
    #READ        
    def read(self, request):
        extdirect_data = self.extract_data(request, 'READ')
        ok, msg = self.pre_read(extdirect_data)
        if ok:           
            return self.store.query(**extdirect_data)
        else:
            return self.failure(msg)
    
    #UPDATE    
    @transaction.commit_manually
    def update(self, request):
        extdirect_data = self.extract_data(request, 'UPDATE')
        
        ok, msg = self.pre_update(extdirect_data)
        if not ok:
            return self.failure(msg)
        
        ids = []
        success = True
        records = extdirect_data[1]
        sid = transaction.savepoint()
        
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
            res = self.store.query(self.model.objects.filter(pk__in=ids))
            res['message'] = "Records updated"
            return res
        else:
            transaction.savepoint_rollback(sid)
            return self.failure("There was an error while trying to save some of the records.")
    
    #DESTROY        
    def destroy(self, request):
        ids = self.extract_data(request, 'DESTROY')
        
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
    
