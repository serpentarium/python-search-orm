"""
QuerySet ...
"""
from pso.q import Q
# from copy import copy
from pso.utils import copy_self


class BaseQuerySet():
    """
    Base queryset class. You shoud be itheritent from it.
    """

    __slots__ = ('_offset', '_limit', '_query', '_model', '_prefetch')

    def __init__(self, model=None):
        self._offset = 0
        self._limit = None
        self._query = None
        self._model = model
        self._prefetch = False

    def __repr__(self):
        return "<{model_name} QuerySet: {qs_repr} | {limit}{offset}>".format(
            model_name=self._model.__name__,
            qs_repr=repr(self._query),
            limit=" LIMIT {}".format(self._limit) if self._limit else '',
            offset=" OFFSET {}".format(self._offset) if self._offset else '',
        )

    def __copy__(self):
        new_one = type(self)()
        for attr in self.__slots__:
            setattr(new_one, attr, getattr(self, attr))
        return new_one

    @copy_self
    def filter(new_qs, *args, **kwargs):
        """
        Universal search by filtering. ...
        """
        if new_qs._query is None:
            new_qs._query = Q(*args, **kwargs)
        else:
            new_qs._query = new_qs._query & Q(*args, **kwargs)
        return new_qs

        # Shoud correct work with Q(), ModelFields, and vanilla **kwargs

    def __call__(self, *args, **kwargs):
        return self.filter(*args, **kwargs)

    @copy_self
    def prefetch(self):
        self._prefetch = True

    @copy_self
    def _slice(new_qs, offset=None, limit=None):
        new_qs._offset = offset
        new_qs._limit = limit
        return new_qs

    def paginate(self, page, per_page=None):
        """Set limit and offset"""
        return self._slice(offset=page * per_page, limit=per_page)

    def __getitem__(self, key):
        if isinstance(key, slice):  # Sequence-like slice loockup
            return self._slice(key.start, key.stop)
            # Step is currently unsupported

        return super(self, BaseQuerySet).__getitem__(key)

    def _check_search_condition(self):
        """ Check for excluding queries. Negative limit etc."""
        pass
