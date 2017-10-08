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
from collections import namedtuple
from collections import defaultdict
import logging
from datetime import datetime

from pso.constants import NoValue
from pso.constants import Operator
from pso.constants import Condition
from pso.range import Range
from pso.range import range_sort_func


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def log_this(func):
    msg_template = "{}: \033[32m{}\033[39m({}, {}) \033[33m=\033[39m {}"

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        log.debug(msg_template.format(
            datetime.now(),
            func.__name__,
            args,
            kwargs,
            res,
        ))
        return res
    return wrapper


class QComparisonMixin():
    """QComparisonMixin - defines comparsion magic for Q objects"""

    @log_this
    def _merge_ranges(self):
        # TODO: Split this func.
        if self.is_leaf or not self.is_field:
            return self
        tmp_childs = set(self.childs)
        ranges = filter(lambda x: x.operation is Condition.RANGE, tmp_childs)
        previous = None

        # TODO: move sort func, to utils
        for q in sorted(ranges, key=range_sort_func):
            try:
                # TODO predefine 'previos'
                merged_range = previous.value.merge(q.value, self.operator)

                tmp_childs.discard(q)
                tmp_childs.discard(previous)
                # !important: remove first
                tmp_childs.add(q._replace(
                    value=merged_range,
                ))
            except:
                continue
            finally:
                previous = q

        if len(tmp_childs) == 1:  # Remove unusefull parent
            child = tmp_childs.pop()
            kwargs = {}
            if child.field:
                kwargs['field'] = child.field

            return self._replace(
                childs=(),
                value=child.value,
                operation=child.operation,
                operator=Q.DEFAULT_OPERATOR,
                boost=self.boost * child.boost,
                inverted=self.inverted ^ child.inverted,
                **kwargs
            )
        else:
            return self._replace(childs=tuple(tmp_childs))

    def __lt__(self, value):
        return self\
            ._make_op(Condition.RANGE, Range(to=value, to_incl=False))\
            ._merge_ranges()

    def __le__(self, value):
        return self\
            ._make_op(Condition.RANGE, Range(to=value, to_incl=True))\
            ._merge_ranges()

    @log_this
    def __eq__(self, value):
        # Allow comparing of non-field Q values
        if getattr(self, "qtype", BaseQ.FIELD) != BaseQ.FIELD:
            return tuple(self) == value
        return self._make_op(Condition.EQ, value)

    @log_this
    def __ne__(self, value):
        # Allow comparing of non-field Q values
        if getattr(self, "qtype", BaseQ.FIELD) != BaseQ.FIELD:
            return tuple(self) != value
        return -self._make_op(Condition.EQ, value)

    def __gt__(self, value):
        return self\
            ._make_op(Condition.RANGE, Range(fr=value, fr_incl=False))\
            ._merge_ranges()

    def __ge__(self, value):
        return self\
            ._make_op(Condition.RANGE, Range(fr=value, fr_incl=True))\
            ._merge_ranges()


class QShiftContainsMixin:
    """
    Unusefull, because IN applied automaticly for multifield
    """

    def __rshift__(self, value):
        return self._make_op(Condition.IN, value)

    __rlshift__ = __rshift__

    def __lshift__(self, value):
        return self._make_op(Condition.IN, value)

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
    'QTuple',
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

    # Logical tree
    def __invert__(self):
        return self._replace(inverted=not self.inverted)

    def __neg__(self):
        return self._replace(inverted=True)

    def __pos__(self):
        return self._replace(inverted=False)

    def __and__(self, other):
        return self._merge_condition(other, Operator.AND)

    def __or__(self, other):
        return self._merge_condition(other, Operator.OR)


class Q(QComparisonMixin, QShiftContainsMixin, QNumericBoostMixin, BaseQ):

    def __hash__(self):
        return hash(tuple(self))

    @log_this
    def _make_op(self, operation, value):
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
            return self._replace(
                field=self.is_field,
                childs=self.childs + (q))._merge_ranges()
        else:
            raise ValueError(
                'Can not use comparsion of complex Q with multuple fields')

    @log_this
    def _merge_condition(self, other, operator=Operator.AND):
        if not isinstance(other, Q):
            return NotImplemented

        childs = set()
        same_invertion = self.inverted == other.inverted

        unpack_and_join(childs, self, same_invertion, operator)
        unpack_and_join(childs, other, same_invertion, operator)

        merge_by_field(childs, operator)

        childs = {q._merge_ranges() for q in childs}

        if len(childs) == 1:
            return childs.pop()._merge_ranges()

        return Q(operator, childs=tuple(childs))._merge_ranges()


def unpack_and_join(nested, obj, inv, operator):
    if obj.qtype == Q.AGGREGATION and obj.operator == operator and inv:
        nested |= {q if q.is_field else q._replace(field=obj.field)
                   for q in obj.childs}
    else:
        nested.add(obj)


@log_this
def merge_by_field(q_set, op):
    mapper = defaultdict(set)

    for q in q_set:
        field = q.is_field
        if field:
            mapper[field].add(q)

    for field, queries in mapper.items():
        if len(queries) == 1:
            continue

        q_set -= queries
        q_set.add(Q(
            field=field,
            operator=op,
            childs=(q._replace(field=None) for q in queries)
        ))
