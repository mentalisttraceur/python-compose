# SPDX-License-Identifier: 0BSD
# Copyright 2019 Alexander Kozhevnikov <mentalisttraceur@gmail.com>

"""The classic ``compose``, with all the Pythonic features."""

from inspect import isawaitable as _isawaitable

try:
    from reprlib import recursive_repr as _recursive_repr
    _recursive_repr_if_available = _recursive_repr()
except ImportError:
    def _recursive_repr_if_available(function):
        return function


__all__ = ('compose', 'acompose')
__version__ = '1.2.0'


def _name(obj):
    return type(obj).__name__


class compose(object):
    """Function composition: compose(f, g)(...) is equivalent to f(g(...))."""

    def __init__(self, *functions):
        """Initialize the composed function.

        Arguments:
            *functions: Functions (or other callables) to compose.
                Instances of ``compose`` are flattened, not nested.

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

    def __call__(self, /, *args, **kwargs):
        """Call the composed function."""
        result = self.__wrapped__(*args, **kwargs)
        for function in self._wrappers:
            result = function(result)
        return result

    def __add__(self, other):
        """Compose using '+' operator."""
        if isinstance(other, compose):
            return compose(*self.functions, *other.functions)
        elif callable(other):
            return compose(*self.functions, other)
        else:
            raise ValueError("Can only compose callables and 'compose' instances.")

    @_recursive_repr_if_available
    def __repr__(self):
        """Represent the composed function as an unambiguous string."""
        arguments = ', '.join(map(repr, reversed(self.functions)))
        return _name(self) + '(' + arguments + ')'

    @property
    def functions(self):
        """Read-only tuple of the composed callables, in order of execution."""
        return (self.__wrapped__,) + tuple(self._wrappers)


class acompose(compose):
    """Asynchronous function composition.

    This variant supports both regular and ``async`` functions.
    The composed function must always be called with ``await``,
    even if none of the functions being composed are ``async``.
    """

    async def __call__(self, /, *args, **kwargs):
        """Call the composed function."""
        result = self.__wrapped__(*args, **kwargs)
        if _isawaitable(result):
            result = await result
        for function in self._wrappers:
            result = function(result)
            if _isawaitable(result):
                result = await result
        return result


# Portability to some minimal Python implementations:
try:
    compose.__name__
except AttributeError:
    compose.__name__ = 'compose'
    acompose.__name__ = 'acompose'
