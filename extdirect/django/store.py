from django.core.serializers import serialize, python
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from StringIO import StringIO
from django.utils.encoding import smart_str, smart_unicode
from django.utils import datetime_safe

class Serializer(python.Serializer):
    """    
    """
    def start_serialization(self, total):
        self._current = None
        self.objects = {
            self.meta['root']: [],
            self.meta['total']: total
        }

    def end_serialization(self):
        pass

    def start_object(self, obj):
        self._current = {}
        
    def end_object(self, obj):
        rec = self._current
        rec['id'] = smart_unicode(obj._get_pk_val(), strings_only=True)
        
        for extra in self.extras:
                rec[extra[0]] = extra[1](obj)
                
        self.objects[self.meta['root']].append(rec)
        self._current = None        
        
    def handle_field(self, obj, field):
        self._current[field.name] = smart_unicode(getattr(obj, field.name), strings_only=True)

    def handle_fk_field(self, obj, field):
        related = getattr(obj, field.name)
        if related is not None:
            if field.rel.field_name == related._meta.pk.name:
                # Related to remote object via primary key
                related = related._get_pk_val()
            else:
                # Related to remote object via other field
                related = getattr(related, field.rel.field_name)
        self._current[field.name] = self._current[field.name+'_id'] = smart_unicode(related, strings_only=True)         

    def handle_m2m_field(self, obj, field):
        if field.creates_table:
            self._current[field.name] = self._current[field.name+'_ids'] = [smart_unicode(related._get_pk_val(), strings_only=True)
                               for related in getattr(obj, field.name).iterator()]        
    
    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.get("stream", StringIO())
        self.selected_fields = options.get("fields")
        
        self.local_fields = options.get("local")
        
        self.meta = options.get('meta', dict(root='records', total='total'))
        self.extras = options.get('extras', [])
        
        total = options.get("total", queryset.count())        
        self.start_serialization(total)
                        
        for obj in queryset:
            if self.local_fields:
                fields = obj._meta.local_fields
            else:
                fields = obj._meta.fields
                
            self.start_object(obj)
            for field in fields:
                if field.serialize:
                    if field.rel is None:
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in obj._meta.many_to_many:
                if field.serialize:
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            self.end_object(obj)
        self.end_serialization()
        return self.getvalue()    

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
