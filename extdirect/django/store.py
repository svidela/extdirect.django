from django.core.serializers import serialize
from django.core.paginator import Paginator, InvalidPage, EmptyPage

class ExtDirectStore(object):
    """
    Implement the server-side needed to load an Ext.data.DirectStore
    Usage::
    
    IMPORTANT: len=1 (python) and paramsAsHash=true (javascript) are required !!!
    
    @remoting(provider, action='user', len=1)
    def load_users(request):
        data = request.extdirect_post_data[0]
        #Just create an instance of ExtDirectStore with a db model class
        users = ExtDirectStore(User)
        # If ExtJS add any parameter usign baseParams or any other method,
        # you must ensure that all the parameter are accepted by QuerySet.filter
        # http://docs.djangoproject.com/en/dev/ref/models/querysets/
        return users.query(**data)
        
    The ExtJS Direct Store should look like::
    
    new Ext.data.DirectStore({
        paramsAsHash: true, 
        directFn: django.user.load_users,        
        fields: [
            {name: 'first_name'}, 
            {name: 'last_name'}, 
            {name: 'id'}
        ],
        // defaults in django
        root: 'records',
        idProperty: 'id',
        totalProperty: 'total',
        ...
    })    
    """
    
    def __init__(self, model, extras=[], root='records', total='total', start='start', limit='limit', sort='sort', dir='dir'):
        self.model = model        
        self.root = root
        self.total = total
        self.extras = extras
        
        # paramNames
        self.start = start
        self.limit = limit
        self.sort = sort
        self.dir = dir
        
    def query(self, qs=None, **kw):                
        paginate = False
        total = None
        order = False
        
        if kw.has_key(self.start) and kw.has_key(self.limit):
            start = kw.pop(self.start)
            limit = kw.pop(self.limit)
            paginate = True
            
        if kw.has_key(self.sort) and kw.has_key(self.dir):
            sort = kw.pop(self.sort)
            dir = kw.pop(self.dir)
            order = True
            
            if dir == 'DESC':
                sort = '-' + sort
                
        if not qs is None:
            # Don't use queryset = qs or self.model.objects
            # because qs could be empty list (evaluate to False)
            # but it's actually an empty queryset that must have precedence
            queryset = qs
        else:
            queryset = self.model.objects
            
        queryset = queryset.filter(**kw)
        
        if order:
            queryset = queryset.order_by(sort)
                
        if not paginate:
            objects = queryset
        else:
            paginator = Paginator(queryset, limit)
            total = paginator.count
            
            try:                
                page = paginator.page(start + 1)
            except (EmptyPage, InvalidPage):
                #out of range, deliver last page of results.
                page = paginator.page(paginator.num_pages)
            
            objects = page.object_list
            
        return self.serialize(objects, total)
        
    def serialize(self, queryset, total=None):        
        meta = {
            'root': self.root,
            'total' : self.total
        }
        res = serialize('extdirect', queryset, meta=meta, extras=self.extras)
        return res
