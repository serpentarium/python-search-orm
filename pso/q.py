"""
Prototype of immutable Query entity objects

Will be used in fields classes, E.G:

user_qs = categories in Article.cateory & Article.user == 777
not_published = Q(published__gt=datetime.now()) | Q(visible=False)
published = Q(published__le=datetime.now()) & Q(visible=True)


Article.filter(not_published)[0, 100]
Article.filter(published)
Article.filter(Article.user_id == Article.edited_by)
"""
from functools import reduce
from functools import wraps
from collections.abc import Iterable
from collections import namedtuple
import ipdb


class _NoValue:
    """
    To check when value is explicitly None or False
    """
    @staticmethod
    def __bool__():
        return False


NoValue = _NoValue()


class Operator:
    """Constants to define join operators."""
    AND = 'AND'
    OR = 'OR'
    XOR = 'XOR'


class Condition:
    """Constants to define condition operators"""
    LT = 'lt'
    LE = 'le'
    EQ = 'eq'
    NE = 'ne'
    GT = 'gt'
    GE = 'ge'
    IN = 'in'
    RANGE = 'range'


RANGE_CONDITIONS = [
    Condition.LT,
    Condition.LE,
    Condition.GT,
    Condition.GE,
]


class Range(namedtuple('Range', ['fr', 'to', 'fr_incl', 'to_incl'])):

    def __new__(cls, fr=NoValue, to=NoValue, fr_incl=False, to_incl=False):
        return super(Range, cls).__new__(cls, fr, to, fr_incl, to_incl)

    def _check_overlap(self, other):
        # ipdb.set_trace(context=50)
        if self.to and other.fr:
            incl = (self.to_incl or other.fr_incl)
            if other.fr > self.to or (other.fr == self.to and not incl):
                return False

        if self.fr and other.to:
            incl = (self.fr_incl or other.to_incl)
            if self.fr > other.to or (self.fr == other.to and not incl):
                return False

        return True

    @staticmethod
    def _merge(func, v1, v2):
        if v1[0] and v2[0]:
            return func(v1, v2)
        else:
            return v1 if v1[0] else v2

    def merge(self, other, operator):
        if operator is Operator.OR:
            return self.__or__(other)
        else:
            return self.__and__(other)

    def __and__(self, other):
        """
        Merge range with AND operator
        """
        # ipdb.set_trace(context=50)
        if not self._check_overlap(other):
            raise ValueError("Can not merge non overlapped ranges")

        fr, fr_incl = self._merge(
            max, (self.fr, not self.fr_incl), (other.fr, not other.fr_incl))
        fr_incl = not fr_incl

        to, to_incl = self._merge(
            min, (self.to, self.to_incl), (other.to, other.to_incl))

        return Range(fr, to, fr_incl, to_incl)

    def __or__(self, other):
        """
        Merge range with AND operator
        """
        if not self._check_overlap(other):
            raise ValueError("Can not merge non overlapped ranges")

        fr, fr_incl = self._merge(
            min, (self.fr, not self.fr_incl), (other.fr, not other.fr_incl))
        fr_incl = not fr_incl

        to, to_incl = self._merge(
            max, (self.to, self.to_incl), (other.to, other.to_incl))

        return Range(fr, to, fr_incl, to_incl)

    @classmethod
    def from_range(cls, r):
        """
        Ability to use Python's standart range object

        Model.field_name == range(0, 100) -> {0 TO 100}
        Model.field_name == range(0, 100, True) -> [0 TO 100]
        """
        include = (True, True) if r.step is True else (False, False)
        cls(r.start, r.end, *include)


def unpack_magic(method):
    """
    Method decorator used to unpack Iterable items,
    create and return multiple same Q objects for each value

    E.G:
    Recipe.filter(*Recipe.category == ['cat1', 'cat2', 'cat3'])
    """
    @wraps(method)
    def unpack(self, value):
        # String is value by itself, skip unpack.
        if isinstance(value, Iterable) and not isinstance(value, str):
            # unpack lists here
            return tuple(method(self, item) for item in value)
        else:
            return method(self, value)
    return unpack


class QComparisonMixin():
    """QComparisonMixin - defines comparsion magic for Q objects"""

    def _merge_ranges(self):
        # ipdb.set_trace(context=50)
        if self.is_leaf or not self.is_field:
            return self
        childs = list(self.childs)
        ranges = filter(lambda x: x.operation is Condition.RANGE, childs)
        previous = None

        for q in sorted(ranges, key=lambda x: (x.value.fr is not NoValue, x.value.fr, x.value.to is NoValue, x.value.to)):
            try:
                # TODO predefine 'previos'
                childs.append(
                    q._replace(value=previous.value.merge(q.value, self.operator))
                )
                childs.remove(q)
                childs.remove(previous)
            except:
                continue
            finally:
                previous = q
        return self._replace(childs=tuple(childs))

    @unpack_magic
    def __lt__(self, value):
        return self\
            ._make_q_operation(Condition.RANGE, Range(to=value, to_incl=False))\
            ._merge_ranges()

    @unpack_magic
    def __le__(self, value):
        return self\
            ._make_q_operation(Condition.RANGE, Range(to=value, to_incl=True))\
            ._merge_ranges()

    @unpack_magic
    def __eq__(self, value):
        return self._make_q_operation(Condition.EQ, value)

    @unpack_magic
    def __ne__(self, value):
        return self._make_q_operation(Condition.NE, value)

    @unpack_magic
    def __gt__(self, value):
        return self\
            ._make_q_operation(Condition.RANGE, Range(fr=value, fr_incl=False))\
            ._merge_ranges()

    @unpack_magic
    def __ge__(self, value):
        print(value)
        print(Range(10, 20, False, False))
        return self\
            ._make_q_operation(Condition.RANGE, Range(fr=value, fr_incl=True))\
            ._merge_ranges()

    def __contains__(self, value):
        """To use reverse in operator as contains operation

        Can be working later:
        >>> 'teacher' in Profile.bio
        >>> iterable in Q('searchfield')  # Bad use case
        Not working:
        >>> Q('somefield') in iterable
        Because there is no reverse __contains__ method or fallback.
        __contains__ shoud return boolean value
        """
        return self._make_q_operation(Condition.IN, value)


class QShiftContainsMixin:
    """Used to search by IN
    Like:
    Q('category') >> ['commedy', 'dramma', 'western']
    Q('tags') << 'sometag'
    """

    def __rshift__(self, value):
        return self._make_q_operation(Condition.IN, value)

    __rlshift__ = __rshift__

    def __lshift__(self, value):
        return self._make_q_operation(Condition.IN, value)

    __rrshift__ = __lshift__


class QNumericBoostMixin:
    """
    Used to boost fields by multiplying them.
    Q('OR', qs * 2, tags / 4
    """
    #  TODO: Immutable. Return new object

    def __mul__(self, value):
        return self._replace(boost=self.boost * value)


def _is_onefield(q1, q2):
    if not q1:
        return False
    if q2:
        return q1 if q1.is_field == q2.is_field else False
    else:
        return q1 if q1.field else False


QTuple = namedtuple(
    'BaseBaseQ',
    [
        'field', 'operation', 'value', 'operator', 'inverted',
        'childs', 'boost'
    ]
)


class BaseQ(QTuple):
    """Immutable query object"""

    CONDITION = 'CONDITION'
    AGGREGATION = 'AGGREGATION'
    FIELD = 'FIELD'

    DEFAULT_OPERATOR = Operator.AND

    @property
    def is_leaf(self):
        return len(self.childs) == 0

    @property
    def qtype(self):
        if len(self.childs):
            return self.AGGREGATION
        elif self.value != NoValue:
            return self.CONDITION
        else:
            return self.FIELD

    @property
    def is_field(self):
        if self.qtype == self.AGGREGATION:
            return reduce(_is_onefield, self.childs)
        else:
            return self.field

    # TODO work with namedtuple
    def __new__(cls, *args, field=None, operation=None, value=NoValue,
                childs=(), inverted=False, operator=DEFAULT_OPERATOR,
                boost=1, **kwargs):
        args = list(args)

        if len(args) and isinstance(args[0], str):
            if args[0] in ['AND', 'OR']:
                operator = args.pop(0)
            else:
                field = args.pop(0)

        # simple constructor
        if field or childs or value is not NoValue:
            childs = tuple(childs)
            return super().__new__(
                cls,
                field=field,
                operation=operation,
                value=value,
                operator=operator,
                inverted=inverted,
                childs=childs,
                boost=boost,
            )

        # magic
        else:
            childs = []
            # Nested Q objects.
            if args:
                if all(isinstance(arg, cls) for arg in args):
                    childs = args
                else:
                    raise ValueError("Can not agregate non-Q values")

            # Kwargs multiquery
            for key, value in kwargs.items():  # R
                item = '__'.join(key.split('__')[0:-1]) if '__' in key else key
                operation = key.split('__')[-1] if '__' in key else 'eq'
                childs.append(
                    cls(field=item, operation=operation, value=value)
                )

            if len(childs) == 1:  # one Kwarg with no nested Q
                return childs[0]

            return cls(operator, childs=tuple(childs))

    def __repr__(self):
        is_not = ' NOT' if self.inverted else ''
        boost = '^{}'.format(self.boost) if self.boost != 1 else ''
        field = self.field or ''
        operation = self.operation or ''
        if self.childs:
            value = ' '.join([
                '(',
                ' {} '.format(self.operator).join(repr(q) for q in self.childs),  # noqa
                ')'
            ])
        else:
            value = repr(self.value)

        template = '<Q {field!s}{boost}{is_not} {operation} {value}>'  # noqa
        return template.format(
            field=field,
            boost=boost,
            operation=operation,
            is_not=is_not,
            value=value
        )

    def _serialize_as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    # Logical tree
    def __invert__(self):
        self.inverted = not self.inverted
        return self

    def __and__(self, other):
        return self._merge_condition(other, Operator.AND)

    def __or__(self, other):
        return self._merge_condition(other, Operator.OR)


class Q(QComparisonMixin, QShiftContainsMixin, QNumericBoostMixin, BaseQ):

    def _make_q_operation(self, operation, value):
        print(self, operation, value)
        if self.is_leaf:
            if self.operation:
                # Merge conditions
                return Q(
                    field=self.field,
                    childs=(
                        self._replace(field=None),
                        Q(operation=operation, value=value)
                    )
                )._merge_ranges()
            # Add operation to existing Q object
            return self._replace(operation=operation, value=value)
            # TODO: maybe check all childs field ... and in some case append
        elif self.is_field:
            q = Q(operation=operation, value=value)
            return self._replace(field=self.is_field, child=self.childs + (q))._merge_ranges()
        else:
            raise ValueError(
                'Can not use comparsion of complex Q with multuple fields')

    def _merge_condition(self, other, operator=Operator.AND):
        if not isinstance(other, Q):
            return NotImplemented

        childs = []
        same_invertion = self.inverted == other.inverted

        if self.qtype == Q.AGGREGATION\
           and self.operator == operator and same_invertion:
            childs.extend(list(self.childs))
        else:
            childs.append(self)

        if other.qtype == Q.AGGREGATION\
           and other.operator == operator and same_invertion:
            childs.extend(list(other.childs))
        else:
            childs.append(other)

        childs = self._merge_ranges(childs)

        return Q(operator, childs=tuple(childs))._merge_ranges()
