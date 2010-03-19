from django.core.serializers import serialize
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from metadata import meta_fields

class ExtDirectStore(object):
    """
    Implement the server-side needed to load an Ext.data.DirectStore
    """
    
    def __init__(self, model, extras=[], root='records', total='total', \
                 success='success', message='message', start='start', limit='limit', \
                 sort='sort', dir='dir', metadata=False, id_property='id', \
                 mappings={}, sort_info={}, custom_meta={}, exclude_fields=[], \
                 extra_fields=[], get_metadata=None):
        
        self.model = model        
        self.root = root
        self.total = total
        self.success = success
        self.extras = extras        
        self.id_property = id_property
        self.message = message
        self.exclude_fields = exclude_fields
        
        # paramNames
        self.start = start
        self.limit = limit
        self.sort = sort
        self.dir = dir
        
        self.metadata = {}
        if metadata:            
            fields = meta_fields(model, mappings, exclude_fields, get_metadata) + extra_fields            
            self.metadata = {
                'idProperty': id_property,
                'root': root,
                'totalProperty': total,
                'successProperty': success,
                'fields': fields,
                'messageProperty': message
            }
            if sort_info:
                self.metadata.update({'sortInfo': sort_info})
                
            self.metadata.update(custom_meta)        
        
    def query(self, qs=None, metadata=True, **kw):                
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
            total = queryset.count()
        else:
            paginator = Paginator(queryset, limit)
            total = paginator.count
            
            try:                
                page = paginator.page(start / limit + 1)
            except (EmptyPage, InvalidPage):
                #out of range, deliver last page of results.
                page = paginator.page(paginator.num_pages)
            
            objects = page.object_list
            
        return self.serialize(objects, metadata, total)
        
    def serialize(self, queryset, metadata=True, total=None):        
        meta = {
            'root': self.root,
            'total' : self.total,
            'success': self.success
        }        
        res = serialize('extdirect', queryset, meta=meta, extras=self.extras,
                        total=total, exclude_fields=self.exclude_fields)
        
        if metadata and self.metadata:            
            res['metaData'] = self.metadata        
        
        return res
