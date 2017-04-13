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
        # TODO rewrite queryset_class inheritance
        attr_dict['_fields'] = []
        attr_dict['_stored_fields'] = []
        queryset_class = attr_dict.get('__queryset_class__', )
        for base in bases:
            if issubclass(base, BaseModel):
                # TODO inherit fields
                if not queryset_class:
                    queryset_class = base.__queryset_class__
        if not queryset_class:
            queryset_class = BaseQuerySet

        fields = []
        stored_fields = []

        for attr, val in attr_dict.items():
            if isinstance(val, list) and len(val) == 1 \
               and isinstance(val[0], BaseField):
                # this allows to define models like
                # tage = list(TextField())
                val = val[0]
                attr_dict[attr] = val  # replace attr in object
                val.multi_valued = True

            if isinstance(val, BaseField):

                if not val.name:
                    val.name = attr
                fields.append(attr)
                if val.store:
                    stored_fields.append(attr)

        attr_dict['_fields'] = fields
        attr_dict['_stored_fields'] = stored_fields
        attr_dict['_cache'] = {}

        cls = super().__new__(meta, name, bases, attr_dict)

        # Bind QuerySet  # TODO check this
        setattr(cls, 'objects', queryset_class(cls))
        return cls


class BaseModel(metaclass=ModelMetaClass):
    """Base class for EngineSpecific models"""

    def __init__(self, **kwargs):
        self._cache = {}
        for key, arg in kwargs.items():
            if key in self._fields:
                self._cache[key] = arg

    @classmethod
    def get_fields(cls):
        print(cls, cls._fields)
        return (getattr(cls, name) for name in cls._fields)

    def __iter__(self):
        """Only filed with data to emulate dict behavior"""
        for name in self._fields:
            yield name, self[name]

    def __repr__(self):
        return "<Model: {0.__class__.__name__}>".format(self)

    def __getitem__(self, key):
        return self._cache[key]

    def to_index(self):
        # return self._cache
        arr = {}
        for name in self._fields:
            field = getattr(self.__class__, name)
            if name == '_version_':
                continue
            if field.multi_valued:
                arr[name] = [field.to_index(val)
                             for val in self._cache.get(name, [])]
            else:
                arr[name] = field.to_index(self._cache.get(name))
        return arr
