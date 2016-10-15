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


class QComparisonMixin():
    """QComparisonMixin - defines comparsion magic for Q objects"""

    def __lt__(self, value):
        return self._make_q_operation('lt', value)

    def __le__(self, value):
        return self._make_q_operation('le', value)

    def __eq__(self, value):
        return self._make_q_operation('eq', value)

    def __ne__(self, value):
        return self._make_q_operation('ne', value)

    def __gt__(self, value):
        return self._make_q_operation('gt', value)

    def __ge__(self, value):
        return self._make_q_operation('ge', value)

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
        return self._make_q_operation('in', value)


def _is_onefield(q1, q2):
    if q2:
        return q1.field if q1.field == q2.field else False
    else:
        return q1.field if q1 else False


class BaseQ(QComparisonMixin):
    """Immutable query object"""

    CONDITION = 'CONDITION'
    AGGREGATION = 'AGGREGATION'

    DEFAULT_OPERATOR = 'AND'

    __slots__ = ('_field', '_operation', '_value', '_operator',
                 '_inverted', '_childs')

    @property
    def is_leaf(self):
        return len(self._childs) == 0

    @property
    def qtype(self):
        return self.AGGREGATION if len(self._childs) else self.CONDITION

    @property
    def inverted(self):
        return self._inverted

    @property
    def field(self):
        if self.qtype == self.AGGREGATION:
            reduce(_is_onefield, self._childs)
        else:
            return self._field

    def __new__(cls, *args, _field=None, _operation=None, _value=None,
                _childs=(), _inverted=False, _operator=DEFAULT_OPERATOR,
                **kwargs):
        args = list(args)
        if len(args) and isinstance(args[0], str):
            if args[0] in ['AND', 'OR']:
                _operator = args.pop(0)
            else:
                _field = args.pop(0)

        # simple constructor
        if _field or _childs:
            self = super().__new__(cls)
            self._field = _field
            self._operation = _operation
            self._value = _value
            self._childs = tuple(_childs)
            self._inverted = _inverted
            self._operator = _operator
            return self

        # magic
        else:
            childs = []

            # Nested Q objects.
            if args:
                if all(isinstance(arg, cls) for arg in args):
                    childs = args
                else:
                    raise ValueError("Err")

            # Kwargs multiquery
            for key, value in kwargs.items():  # R
                item = '__'.join(key.split('__')[0:-1]) if '__' in key else key
                operation = key.split('__')[-1] if '__' in key else 'eq'
                childs.append(
                    cls(_field=item, _operation=operation, _value=value)
                )

            if len(childs) == 1:  # one Kwarg with no nested Q
                return childs[0]

            return cls(_operator, _childs=tuple(childs))

    def __repr__(self):
        is_not = 'NOT' if self._inverted else ''
        if self.qtype == Q.CONDITION:
            template = "<Q {0._field!s} {is_not} {0._operation!s} {0._value!r}>"  # noqa
        else:
            template = "<Q {0._operator!s} {is_not} {0._childs!r}>"  # R
        return template.format(self, is_not=is_not)

    def _serialize_as_dict(self):
        return {
            '_field': self._field,
            '_operation': self._operation,
            '_value': self._value,
            '_operator': self._operator,
            '_inverted': self._inverted,
            '_childs': self._childs,
        }

    # Logical tree
    def __invert__(self):
        kwargs = self._serialize_as_dict()
        kwargs['_inverted'] = not kwargs['_inverted']
        return Q(**kwargs)

    def __and_or(self, other, operator='AND'):
        if not isinstance(other, Q):
            return NotImplemented

        childs = []
        same_invertion = self._inverted == other._inverted
        if self.qtype == Q.AGGREGATION\
           and self._operator == operator and same_invertion:
            childs.extend(list(self._childs))
        else:
            childs.append(self)

        if other.qtype == Q.AGGREGATION\
           and other._operator == operator and same_invertion:
            childs.extend(list(other._childs))
        else:
            childs.append(other)

        return Q(operator, _childs=tuple(childs))

    def __and__(self, other):
        return self.__and_or(other, 'AND')

    def __or__(self, other):
        return self.__and_or(other, 'OR')



class Q(BaseQ, QComparisonMixin):

    def _make_q_operation(self, operation, value):
        if self.is_leaf:
            q = Q(_field=self._field, _operation=operation, _value=value)
            if self._operation:
                # Add operation to existing Q object
                return Q(_childs=(self, q))
            return q
            q = Q(_field=self._field, _operation=operation, _value=value)
            pass
            # TODO: maybe check all childs _field ... and in some case append
        else:
            field = self.field
            if field:
                q = Q(_field=self._field, _operation=operation, _value=value)
                return Q(_childs=self._childs + (q))
            else:
                raise ValueError(
                    'Can not use comparsion of complex Q with multuple fields')


class MutableQ():
    """
    Should help to use magic by registering values in self,
    where is not allowed to return not bool

    E.G:
        10 <= Q('fieldname') <= 99

    Can be used with "with" statement.
    """

    def _reset(self):
        self._field = None
        self._operation = None
        self._value = None
        self._operator = self.DEFAULT_OPERATOR
        self._inverted = False
        self._childs = []

    def __copy__(self):
        return MutableQ(_field=self._field, _operation=self._operation,
                        _value=self._value, _operator=self._operator,
                        _inverted=self._inverted, _childs=self._childs[:])

    # Fields magic
    def _make_q_operation(self, operation, value):
        if self.is_leaf:
            q = MutableQ(_field=self._field, _operation=operation, _value=value)
            if self._operation:
                # Add operation to existing Q object
                return Q(_childs=(self, q))
            return q
            q = Q(_field=self._field, _operation=operation, _value=value)
            pass
            # TODO: maybe check all childs _field ... and in some case append
        else:
            field = self.field
            if field:
                q = Q(_field=self._field, _operation=operation, _value=value)
                return Q(_childs=self._childs + (q))
            else:
                raise ValueError(
                    'Can not use comparsion of complex Q with multuple fields')


# TODO: continue here...

# '''10 <= Q('somefield') <= 99 # Does not work'''
# because it is systax shugar and its impossible
# to overload logic operators in python.
#
# Priority of operators is broken.
# Because bitwise operators has bigger priority than logical
# >>> Q('FFF') >= 17 & Q(olala__gt=999)  # will not work
# >>> (Q('FFF') >= 17) & Q(olala__gt=999)  # will work
# Because '17 & Q'
