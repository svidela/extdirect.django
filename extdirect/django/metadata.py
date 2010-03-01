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
    'ForeignKey'                    : 'int',
    #'ManyToMany'                   : ????
}

def meta_fields(model, mappings):
    fields = model._meta.fields
    result = []
    for field in fields:
        config = {}        
        klass = field.__class__.__name__
        
        config['name'] = field.name
        config['allowBlank'] = field.blank
        
        if mappings.has_key(field.name):
            config['mapping'] = mappings[field.name]
            
        try:
            config['type'] = DJANGO_EXT_MAP[klass]
            if klass == 'DateField':
                config['dateFormat'] = 'Y-m-d'
            if klass == 'TimeField':
                config['dateFormat'] = 'H:i:s'
            if klass == 'DateTimeField':
                config['dateFormat'] = 'Y-m-d H:i:s'
        except:
            #We should check for some method or something in case that the
            #model use a custom Field class.
            raise RuntimeError, "Field class %s not found in DJANGO_EXT_MAP." % klass
                
        if field.has_default():
            config['defaultValue'] = field.default
            
        result.append(config)
        
        if klass == 'ForeignKey':
            config_cpy = config.copy()
            config_cpy['name'] = config['name'] + '_id'
            result.append(config_cpy)
            
    return result
    

