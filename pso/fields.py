"""
PSO fields magic.
"""
from pso.analyzers import AbstractAnalyzer
from pso.q import Q, QComparisonMixin


class FieldMeta(type):
    '''TODO: check if metaclass is required'''


class FieldType():
    """Field type creation shortcut"""
    name = ''  # Shoud be unique
    _analyzers = []
    config = {}

    def __init__(self, name, *analyzers, **settings):
        self.name = name
        for analyzer in analyzers:
            self.add_analyzer(analyzer)
        self._settings = settings

    def __repr__(self):
        return "<{cls}: {name}: {analyzers}>".format(
            analyzers=' | '.join("{!r}".format(a) for a in self._analyzers),
            cls=self.__class__.__name__, name=self.name)

    def __str__(self):
        return str(self.name)

    def add_analyzer(self, analyzer):
        if isinstance(analyzer, AbstractAnalyzer):
            self._analyzers = analyzer
        else:
            raise ValueError("Can not add non Analyzer object")

    @property
    def analyzers(self):
        return self._analyzers


class BaseField(QComparisonMixin):
    """
    Base class for each field
    """
    # TODO: overload equality operators
    #       to return proper Q object instance.
    #       To make filter condition directly on fields

    field_type = None  # <FieldType> for EngineSpecific/UserDefined
    is_pk = False  # Is used to set UniqueId. Used when update index
    field_name = None  # By default populated with <ModelMetaClass>
    _default = None
    store = False
    boost = 1
    index = True
    operations = ()
    multi_valued = False  # E.G. list

    def __init__(self, name=None, default=None, boost=1, store=False,
                 primary_key=False, multi_valued=False, required=False):
        self.field_name = name
        self._default = default
        self.store = store
        self.is_pk = primary_key
        self.boost = boost
        self.multi_valued = multi_valued

    def __repr__(self):
        return "<{0.__class__.__name__}:{0.field_name}>".format(self)

    # Model data-access descriptor behavior.
    def __get__(self, instance, owner_cls):
        if instance is None:  # Access to unbound object
            return self
        return instance._cache.get(self.field_name, self.default)

    def __set__(self, instance, value):
        instance._cache[self.field_name] = value

    @property
    def is_predefined(self):
        return isinstance(self.field_type, str)

    def to_index(self, value):
        """Prepare python value before send"""
        return value or self.default

    def to_python(value):
        """Convert redurned data to Python native obect"""
        return value

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default

    def _make_q_operation(self, operation, value):
        return Q(_field=self.field_name, _operation=operation, _value=value)
