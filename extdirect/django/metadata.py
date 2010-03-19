DJANGO_EXT_MAP = {
    'AutoField'                     : 'int',
    'BooleanField'                  : 'boolean',
    'CharField'                     : 'string',
    'CommaSeparatedIntegerField'    : 'string',
    'DateField'                     : 'date',
    'DateTimeField'                 : 'date',
    'DecimalField'                  : 'float',
    'EmailField'                    : 'string',
    'FileField'                     : 'string',
    'FilePathField'                 : 'string', 
    'FloatField'                    : 'float',
    'ImageField'                    : 'string',
    'IntegerField'                  : 'int',
    'IPAddressField'                : 'string',
    'NullBooleanField'              : 'boolean',
    'PositiveIntegerField'          : 'int',
    'PositiveSmallIntegerField'     : 'int',
    'SlugField'                     : 'string',
    'SmallIntegerField'             : 'int',
    'TextField'                     : 'string',
    'TimeField'                     : 'date',
    'URLField'                      : 'string',
    'XMLField'                      : 'string',
    'ForeignKey'                    : 'string',
    #'ManyToMany'                   : ????
}

def meta_fields(model, mappings={}, exclude=[], get_metadata=None):
    """
    Generate metadata for a given Django model.
    You could provide the `get_metadata` function to generate
    custom metadata for some fields.
    """
    fields = [f for f in model._meta.fields if f.name not in exclude]
    result = []
    for field in fields:
        config = None
        klass = field.__class__.__name__
        if get_metadata:
            #If get_metadata is not None, then it must be a callable object
            #and should return the metadata for a given field or None
            config = get_metadata(field)
            
        if not config:
            #If get_metadata it's None or returned None for a given field
            #then, we try to generate the metadata for that field
            config = {}
            
            if DJANGO_EXT_MAP.has_key(klass):
                config['name'] = field.name
                config['allowBlank'] = field.blank
                
                if mappings.has_key(field.name):
                    config['mapping'] = field.name
                    config['name'] = mappings[field.name]            
            
                config['type'] = DJANGO_EXT_MAP[klass]
                if klass == 'DateField':
                    config['dateFormat'] = 'Y-m-d'
                if klass == 'TimeField':
                    config['dateFormat'] = 'H:i:s'
                if klass == 'DateTimeField':
                    config['dateFormat'] = 'Y-m-d H:i:s'
                    
                if field.has_default():
                    config['defaultValue'] = field.default                
            else:                    
                raise RuntimeError, \
                    "Field class `%s` not found in DJANGO_EXT_MAP. Use `get_metadata` to resolve the field `%s`." % (klass, field.name)
            
        result.append(config)
        
        if klass == 'ForeignKey':
            config_cpy = config.copy()
            config_cpy['name'] = config['name'] + '_id'
            config_cpy['type'] = 'int'
            result.append(config_cpy)
            
    return result
    

