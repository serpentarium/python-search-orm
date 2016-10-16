"""
PSO fields magic.
"""
from functools import wraps
from copy import copy


def copy_self(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
        return function(copy(self), *args, **kwargs)
    return wrapper
