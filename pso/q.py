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


class NoValue:
    """
    To check when value is explicitly None or False
    """


class QComparisonMixin():
    """QComparisonMixin - defines comparsion magic for Q objects"""

    @unpack_magic
    def __lt__(self, value):
        return self._make_q_operation(Condition.LT, value)

    @unpack_magic
    def __le__(self, value):
        return self._make_q_operation(Condition.LE, value)

    @unpack_magic
    def __eq__(self, value):
        return self._make_q_operation(Condition.EQ, value)

    @unpack_magic
    def __ne__(self, value):
        return self._make_q_operation(Condition.NE, value)

    @unpack_magic
    def __gt__(self, value):
        return self._make_q_operation(Condition.GT, value)

    @unpack_magic
    def __ge__(self, value):
        return self._make_q_operation(Condition.GE, value)

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
    if q2:
        return q1.field if q1.field == q2.field else False
    else:
        return q1.field if q1 else False


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
        if field or childs:
            childs = tuple(childs)
            return super().__new__(
                cls,
                field, operation, value, operator,
                inverted, childs, boost

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
                    cls(field=item, operation=operation, _value=value)
                )

            if len(childs) == 1:  # one Kwarg with no nested Q
                return childs[0]

            return cls(operator, childs=tuple(childs))

    def __repr__(self):
        is_not = ' NOT' if self.inverted else ''
        if self.qtype == Q.CONDITION:
            template = "<Q^{0.boost!s} {0.field!s}{is_not} {0.operation!s} {0.value!r}>"  # noqa
        else:
            template = "<Q^{0.boost!s}  {0.operator!s} {is_not} {0.childs!r}>"  # noqa
        return template.format(self, is_not=is_not)

    def _serialize_as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    # Logical tree
    def __invert__(self):
        self.inverted = not self.inverted
        return self

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

        return Q(operator, childs=tuple(childs))

    def __and__(self, other):
        return self._merge_condition(other, Operator.AND)

    def __or__(self, other):
        return self._merge_condition(other, Operator.OR)


class Q(QComparisonMixin, QShiftContainsMixin, QNumericBoostMixin, BaseQ):

    # TODO: rewrite to use namedtuple
    def _make_q_operation(self, operation, value):
        if self.is_leaf:
            q = Q(field=self.field, operation=operation, value=value)
            if self.operation:
                # Merge conditions
                return Q(childs=(self, q))
            # Add operation to existing Q object
            return q
            # q = Q(field=self.field, operation=operation, _value=value)
            # pass
            # TODO: maybe check all childs field ... and in some case append
        elif self.is_field:
            q = Q(field=self.field, operation=operation, value=value)
            return Q(childs=self.childs + (q))
        else:
            raise ValueError(
                'Can not use comparsion of complex Q with multuple fields')
