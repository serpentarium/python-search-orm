"""
Models meta magic here
"""
from pso.fields import BaseField

class ModelMetaClass(type):
    """
    Magic with fields
    """
    def __init__(cls, name, bases, attr_dict):
        super().__init__(name, bases, attr_dict)
        for name, attr in attr_dict.items():
            if isinstance(attr, BaseField):
                if not attr.field_name:
                    attr.field_name = name
                cls._fields.append(attr.field_name)
                if attr.store:
                    cls._stored_fields.append(attr.field_name)




class BaseModel(metaclass=ModelMetaClass):
    """Base class for EngineSpecific models"""
    _fields = []
    _stored_fields = []
    _cache = {}

    def __init__(self, **kwargs):
        for key, arg in kwargs.items():
            if key in self._fields:
                setattr(self, key, arg)

    def get_queryset():
        raise NotImplementedError("Please define get_queryset in Driver!")

    def __iter__(self):
        """Only filed with data to emulate dict behavior"""
        return self._stored_fields

    def __repr__(self):
        return "<Model: {0.__class__.__name__}>".format(self)

    def __getitem__(self, key):
        return _cache[key]

    # def get_object