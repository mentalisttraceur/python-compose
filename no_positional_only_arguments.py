# SPDX-License-Identifier: 0BSD
# Copyright 2019 Alexander Kozhevnikov <mentalisttraceur@gmail.com>

"""The classic ``compose``, with all the Pythonic features."""

__all__ = ('compose', 'acompose')
__version__ = '1.2.6'


from inspect import isawaitable as _isawaitable

from reprlib import recursive_repr as _recursive_repr


def _name(obj):
    return type(obj).__name__


class compose:
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

    def __call__(*args, **kwargs):
        """Call the composed function."""
        if not args:
            raise TypeError("__call__() missing 1 positional argument: 'self'")
        self, args = args[0], args[1:]
        result = self.__wrapped__(*args, **kwargs)
        for function in self._wrappers:
            result = function(result)
        return result

    @_recursive_repr('<...>')
    def __repr__(self):
        """Represent the composed function as an unambiguous string."""
        arguments = ', '.join(map(repr, reversed(self.functions)))
        return _name(self) + '(' + arguments + ')'

    @property
    def functions(self):
        """Read-only tuple of the composed callables, in order of execution."""
        return (self.__wrapped__,) + tuple(self._wrappers)


class acompose:
    """Asynchronous function composition.

    await acompose(f, g)(...) is equivalent to one of

        f(g(...))
        await f(g(...))
        f(await g(...))
        await f(await g(...))

    based on whether f and g return awaitable values.
    """

    def __init__(self, *functions):
        """Initialize the composed function.

        Arguments:
            *functions: Functions (or other callables) to compose.
                Instances of ``acompose`` are flattened, not nested.

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
            if isinstance(function, acompose):
                _functions.append(function.__wrapped__)
                _functions.extend(function._wrappers)
            else:
                _functions.append(function)
        self.__wrapped__ = _functions[0]
        self._wrappers = tuple(_functions[1:])

    async def __call__(*args, **kwargs):
        """Call the composed function."""
        if not args:
            raise TypeError("__call__() missing 1 positional argument: 'self'")
        self, args = args[0], args[1:]
        result = self.__wrapped__(*args, **kwargs)
        if _isawaitable(result):
            result = await result
        for function in self._wrappers:
            result = function(result)
            if _isawaitable(result):
                result = await result
        return result

    __repr__ = compose.__repr__
    functions = compose.functions


# Portability to some minimal Python implementations:
try:
    compose.__name__
except AttributeError:
    compose.__name__ = 'compose'
    acompose.__name__ = 'acompose'
