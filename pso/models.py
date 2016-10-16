"""
Models meta magic here
"""
from pso.fields import BaseField
from pso.query import BaseQuerySet


class ModelMetaClass(type):
    """
    Magic with fields
    """
    def __init__(cls, name, bases, attr_dict):
        attr_dict.setdefault('_fields', [])
        attr_dict.setdefault('_stored_fields', [])

        for name, attr in attr_dict.items():
            if isinstance(attr, BaseField):
                if not attr.field_name:
                    attr.field_name = name
                cls._fields.append(name)
                if attr.store:
                    cls._stored_fields.append(name)

        # Bind QuerySet  # TODO check this
        qs_class = attr_dict.get('queryset_class', BaseQuerySet)
        setattr(cls, 'objects', qs_class(cls))
        super(ModelMetaClass, cls).__init__(name, bases, attr_dict)


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
        return (getattr(cls, name) for name in cls._fields)

    def __iter__(self):
        """Only filed with data to emulate dict behavior"""
        return self._stored_fields

    def __repr__(self):
        return "<Model: {0.__class__.__name__}>".format(self)

    def __getitem__(self, key):
        return self._cache[key]

    # def get_object
