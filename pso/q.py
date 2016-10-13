"""
Prototype of immutable Query entity objects

Will be used in fields classes, E.G:

user_qs = categories in Article.cateory & Article.user == 777
not_published = Q(published__gt=datetime.now()) | Q(visible=False)
published = Q(published__le=datetime.now()) & Q(visible=True)

Article.filter(not_published)[0, 100]
Article.filter(published)
"""


class Q():
    """Immutable query object"""

    CONDITION = 'CONDITION'
    AGGREGATION = 'AGGREGATION'

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

    def __new__(cls, *args, _field=None, _operation=None, _value=None,
                _childs=(), _inverted=False, _operator='AND', **kwargs):
        operator = cls._operator
        args = list(args)
        if len(args) and isinstance(args[0], str):
            if args[0] in ['AND', 'OR']:
                operator = args.pop(0)
            else:
                _field = args.pop(0)

        # simple constructor
        if _field or _childs:
            self = super(Q, cls).__new__(cls)
            self._field = _field
            self._operation = _operation
            self._value = _value
            self._childs = tuple(_childs)
            self._inverted = _inverted
            self._operator = operator
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
                    cls(_field=item, _operation=operation, value=value)
                )

            if len(childs) == 1:  # one Kwarg with no nested Q
                return childs[0]

            return cls(operator, _childs=tuple(childs))

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

    def __and_or(self, value, operator='AND'):
        if not isinstance(value, Q):
            return NotImplemented

        childs = []
        if self.qtype == Q.AGGREGATION and self._operator == operator:
            childs.extend(list(self._childs))
        else:
            childs.append(self)

        if value.qtype == Q.AGGREGATION and value._operator == operator:
            childs.extend(list(value._childs))
        else:
            childs.append(value)

        return Q(operator, _childs=tuple(childs))

    def __and__(self, value):
        return self.__and_or(value, 'AND')

    def __or__(self, value):
        return self.__and_or(value, 'OR')

    # Fields magic
    def _add_operation(self, operation, value):
        if self.is_leaf:
            q = Q(_field=self._field, _operation=operation, _value=value)
            if self._operation:
                return Q(_childs=(self, q))
            return q
        else:
            raise ValueError('Can not use comparsion of complex Q')
            # TODO: maybe check all childs _field ... and in some case append

    def __lt__(self, value):
        return self._add_operation('lt', value)

    def __le__(self, value):
        return self._add_operation('le', value)

    def __eq__(self, value):
        return self._add_operation('eq', value)

    def __ne__(self, value):
        return self._add_operation('ne', value)

    def __gt__(self, value):
        return self._add_operation('gt', value)

    def __ge__(self, value):
        return self._add_operation('ge', value)

    def __contains__(self, value):
        """Q() IN operator

        Reverse contains, which get iterable and return Q
        Working:
        >>> iterable in Q('searchfield')
        Not working:
        >>> Q('somefield') in iterable
        Because there is no reverse __contains__ method or fallback.
        """
        return self._add_operation('in', value)


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
