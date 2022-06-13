# SPDX-License-Identifier: 0BSD
# Copyright 2019 Alexander Kozhevnikov <mentalisttraceur@gmail.com>

"""The classic ``compose``, with all the Pythonic features."""

__all__ = ('compose',)
__version__ = '1.4.3'


try:
    from reprlib import recursive_repr as _recursive_repr
    _recursive_repr_if_available = _recursive_repr('<...>')
except ImportError:
    def _recursive_repr_if_available(function):
        return function


def _name(obj):
    return type(obj).__name__


class compose(object):
    """Function composition: compose(f, g)(...) is equivalent to f(g(...))."""

    def __init__(self, *functions):
        """Initialize the composed function.

        Arguments:
            *functions: Functions (or other callables) to compose.

        Raises:
            TypeError:
                If no arguments are given.
                If any argument is not callable.
        """
        if not functions:
            name = _name(self)
            raise TypeError(repr(name) + ' needs at least one argument')
        _functions = []
        for function in reversed(functions):
            if not callable(function):
                name = _name(self)
                raise TypeError(repr(name) + ' arguments must be callable')
            if isinstance(function, compose):
                _functions.append(function.__wrapped__)
                _functions.extend(function._wrappers)
            else:
                _functions.append(function)
        self.__wrapped__ = _functions[0]
        self._wrappers = tuple(_functions[1:])

    def __call__(*args, **kwargs):
        """Call the composed function."""
        def __call__(self, *args):
            return self, args
        self, args = __call__(*args)
        result = self.__wrapped__(*args, **kwargs)
        for function in self._wrappers:
            result = function(result)
        return result

    def __get__(self, obj, objtype=None):
        """Get the composed function as a bound method."""
        if obj is None:
            return self
        return _BoundMethod(self, obj)

    @_recursive_repr_if_available
    def __repr__(self):
        """Represent the composed function as an unambiguous string."""
        arguments = ', '.join(map(repr, reversed(self.functions)))
        return _name(self) + '(' + arguments + ')'

    @property
    def functions(self):
        """Read-only tuple of the composed callables, in order of execution."""
        return (self.__wrapped__,) + tuple(self._wrappers)


class _BoundMethod(object):
    __slots__ = ('__func__', '__self__', '__weakref__')

    def __init__(self, function, instance):
        self.__func__ = function
        self.__self__ = instance

    def __call__(*args, **kwargs):
        def __call__(self, *args):
            return self, args
        self, args = __call__(*args)
        return self.__func__(self.__self__, *args, **kwargs)

    def __get__(self, obj, objtype=None):
        return self

    def __repr__(self):
        return repr(self.__func__) + '.__get__(' + repr(self.__self__) + ')'

    def __reduce__(self):
        return (_BoundMethod, (self.__func__, self.__self__))

    # Python 2 used these attribute names:
    @property
    def im_func(self):
        return self.__func__
    @property
    def im_self(self):
        return self.__self__


# Portability to some minimal Python implementations:
try:
    compose.__name__
except AttributeError:
    compose.__name__ = 'compose'
