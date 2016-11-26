"""
Models meta magic here
"""
from pso.fields import BaseField
from pso.query import BaseQuerySet


class ModelMetaClass(type):
    """
    Magic with fields
    """

    def __new__(meta, name, bases, attr_dict):
        attr_dict['_fields'] = []
        attr_dict['_stored_fields'] = []
        queryset_class = attr_dict.pop('__queryset_class__', BaseQuerySet)
        fields = []
        stored_fields = []

        for name, attr in attr_dict.items():
            if isinstance(attr, list) and len(attr) == 1 \
               and isinstance(attr[0], BaseField):
                # this allows to define models like
                # tage = list(TextField())
                attr = attr[0]
                attr_dict[name] = attr  # replace attr in object
                attr.multi_valued = True
                print('DEBUG', name, attr)

            if isinstance(attr, BaseField):

                if not attr.name:
                    attr.name = name
                fields.append(name)
                if attr.store:
                    stored_fields.append(name)

            attr_dict['_fields'] = fields
            attr_dict['_stored_fields'] = stored_fields

        cls = super().__new__(meta, name, bases, attr_dict)

        # Bind QuerySet  # TODO check this
        setattr(cls, 'objects', queryset_class(cls))
        return cls


class BaseModel(metaclass=ModelMetaClass):
    """Base class for EngineSpecific models"""
    _fields = []
    _stored_fields = []
    _cache = {}

    def __init__(self, **kwargs):
        for key, arg in kwargs.items():
            if key in self._fields:
                setattr(self, key, arg)

    @classmethod
    def get_fields(cls):
        print(cls, cls._fields)
        return (getattr(cls, name) for name in cls._fields)

    def __iter__(self):
        """Only filed with data to emulate dict behavior"""
        return self._stored_fields

    def __repr__(self):
        return "<Model: {0.__class__.__name__}>".format(self)

    def __getitem__(self, key):
        return self._cache[key]

    # def get_object
