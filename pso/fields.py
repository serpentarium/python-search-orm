"""
PSO fields magic.
"""
from pso.analyzers import AbstractAnalyzer
from pso.q import Q, QComparisonMixin, QShiftContainsMixin


class FieldMeta(type):
    '''TODO: check if metaclass is required'''


class FieldType():
    # integer, long, float, double, date
    """Field type creation shortcut"""
    name = ''  # Shoud be unique
    _analyzers = []
    # config = {}

    @property
    def config(self):
        return self._settings

    def __init__(self, name, *analyzers, **settings):
        self.name = name
        for analyzer in analyzers:
            self.add_analyzer(analyzer)
        self._settings = settings
        self._settings.setdefault('class', name)

    def __repr__(self):
        return "<{cls}: {name}: {analyzers}>".format(
            analyzers=' | '.join("{!r}".format(a) for a in self._analyzers),
            cls=self.__class__.__name__, name=self.name)

    def __str__(self):
        """Used in schema creation. Use representation for debug"""
        return str(self.name)

    def add_analyzer(self, analyzer):
        if isinstance(analyzer, AbstractAnalyzer):
            self._analyzers.append(analyzer)
        else:
            raise ValueError("Can not add non Analyzer object")

    @property
    def analyzers(self):
        return self._analyzers


class BaseField(QComparisonMixin, QShiftContainsMixin):
    """
    Base class for each field
    """
    # TODO: overload equality operators
    #       to return proper Q object instance.
    #       To make filter condition directly on fields

    field_type = None  # <FieldType> for EngineSpecific/UserDefined
    is_pk = False  # Is used to set UniqueId. Used when update index
    name = None  # By default populated with <ModelMetaClass>
    _default = None
    store = False
    boost = 1
    index = True
    required = False
    operations = ()
    multi_valued = False  # E.G. list

    def __init__(self, name=None, default=None, boost=1, index=True,
                 store=False, primary_key=False, multi_valued=False,
                 required=False):
        self.name = name
        self._default = default
        self.store = store
        self.index = index
        self.is_pk = primary_key
        self.boost = boost
        self.multi_valued = multi_valued
        self.required = required or primary_key

    def __repr__(self):
        return "<{0.__class__.__name__}:{0.name}>".format(self)

    # Model data-access descriptor behavior.
    def __get__(self, instance, owner_cls):
        if instance is None:  # Access to unbound object
            return self
        return instance._cache.get(self.name, self.default)

    def __set__(self, instance, value):
        instance._cache[self.name] = value

    @property
    def is_predefined(self):
        return isinstance(self.field_type, str)

    def to_index(self, value):
        """Prepare python value before send"""
        return value or self.default

    def to_python(self, value):
        """Convert redurned data to Python native obect"""
        return value

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default

    def _make_op(self, operation, value):
        return Q(field=self.name, operation=operation, value=value)

    def __mul__(self, value):
        return Q(field=self.name, boost=value)
