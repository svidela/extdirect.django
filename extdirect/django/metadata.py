
DJANGO_EXT_MAP = {
    'CharField'                 : 'string',
    'TextField'                 : 'string',
    'IntegerField'              : 'int',
    'PositiveSmallIntegerField' : 'int',
    'PositiveIntegerField'      : 'int',
    'FloatField'                : 'float',
    'DecimalField'              : 'float',
    'DateField'                 : 'date',
    'EmailField'                : 'string',
    'URLField'                  : 'string',
    'BooleanField'              : 'boolean',
    'AutoField'                 : 'int',    
    'ForeignKey'                : 'int'
    #add more field types
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
        except:
            raise RuntimeError, "Field class %s not found in DJANGO_EXT_MAP." % klass
                
        if field.has_default():
            config['defaultValue'] = field.default
            
        result.append(config)
        
        if klass == 'ForeignKey':
            config_cpy = config.copy()
            config_cpy['name'] = config['name'] + '_id'
            result.append(config_cpy)
            
    return result
    

