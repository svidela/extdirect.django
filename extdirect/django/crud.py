from extdirect.django.store import ExtDirectStore

class ExtDirectCRUD(object):
    
    model = None
    
    #CREATE
    def pre_create(self, request):
        return request.extdirect_post_data[0]        
        
    def post_create(self, obj):
        pass
    
    def _single_create(self, data):
        #id='ext-record-#'
        data.pop("id")

        #convert: u'key' --> 'key'
        values = dict(map(lambda x: (str(x[0]), x[1]), data.items()))

        c = self.model(**values)
        c.save(force_insert=True)
        
        self.post_create(c)
        
        return c.id
    
    def create(self, request):
        extdirect_data = self.pre_create(request)
        ids = []
        if isinstance(extdirect_data, list):
            for data in extdirect_data:
                id = self._single_create(data)
                ids.append(id)
        else:
            id = self._single_create(extdirect_data)
            ids.append(id)
            
            
        ds = self.direct_store()        
        return ds.query(self.model.objects.filter(pk__in=ids))[ds.root]        
        
    #READ
    def pre_read(self, request):
        return request.extdirect_post_data[0]
    
    def direct_store(self):
        return ExtDirectStore(self.model)
        
    def read(self, request):
        extdirect_data = self.pre_read(request)
        return self.direct_store().query(**extdirect_data)
    
    #UPDATE
    def pre_update(self, request):
        return request.extdirect_post_data
        
    def post_update(self, ids):
        pass
    
    def post_single_update(self, obj):
        pass
    
    def _single_update(self, data):
        id = data.pop("id")
        obj = self.model.objects.get(pk=id)
        
        fields = data.keys()
        for field in obj._meta.fields:
            if field.name in fields:
                value = data.pop(field.name)
                obj.__setattr__(field.name, value)

        obj.save()
        
        self.post_single_update(obj)
    
    def update(self, request):
        extdirect_data = self.pre_update(request)
        
        ids = extdirect_data[0]
        records = extdirect_data[1]
        
        if isinstance(records, list):
            #batch update
            for data in records:
                self._single_update(data)
        
        elif isinstance(records, dict):
            #single update
            self._single_update(records)
        
        else:
            raise AttributeError, "Bad parameter"
        
        self.post_update(ids)
        ds = self.direct_store()
        if isinstance(ids, list):
            return ds.query(self.model.objects.filter(pk__in=ids))[ds.root]
        else:
            return ds.query(self.model.objects.filter(pk=ids))[ds.root]
    
    #DESTROY    
    def pre_destroy(self, request):
        return request.extdirect_post_data[0]
        
    def post_destroy(self, id):
        pass
    
    def destroy(self, request):
        id = self.pre_destroy(request)
        
        c = self.model.objects.get(pk=id)
        c.delete()
        
        self.post_destroy(id)
        
        return dict(success=True, message="Object deleted")
