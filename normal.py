# SPDX-License-Identifier: 0BSD
# Copyright 2019 Alexander Kozhevnikov <mentalisttraceur@gmail.com>

"""The classic ``compose``, with all the Pythonic features."""

__all__ = ('compose', 'acompose', 'sacompose')
__version__ = '1.6.2'


from inspect import isawaitable as _isawaitable
from inspect import iscoroutinefunction as _iscoroutinefunction
from reprlib import recursive_repr as _recursive_repr
try:
    from inspect import markcoroutinefunction as _markcoroutinefunction
except ImportError:
    def _markcoroutinefunction(function):
        pass

def _name(obj):
    return type(obj).__name__


class compose:
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
            raise TypeError(_name(self) + '() needs at least one argument')
        _functions = []
        for function in reversed(functions):
            if not callable(function):
                raise TypeError(_name(self) + '() arguments must be callable')
            if isinstance(function, compose):
                _functions.extend(function.functions)
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

    def __get__(self, obj, objtype=None):
        """Get the composed function as a bound method."""
        wrapped = self.__wrapped__
        try:
            bind = type(wrapped).__get__
        except AttributeError:
            return self
        bound_wrapped = bind(wrapped, obj, objtype)
        if bound_wrapped is wrapped:
            return self
        bound_self = type(self)(bound_wrapped)
        bound_self._wrappers = self._wrappers
        return bound_self

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

        Raises:
            TypeError:
                If no arguments are given.
                If any argument is not callable.
        """
        if not functions:
            raise TypeError(_name(self) + '() needs at least one argument')
        _functions = []
        for function in reversed(functions):
            if not callable(function):
                raise TypeError(_name(self) + '() arguments must be callable')
            if isinstance(function, (acompose, sacompose)):
                _functions.extend(function.functions)
            else:
                _functions.append(function)
        self.__wrapped__ = _functions[0]
        self._wrappers = tuple(_functions[1:])
        _markcoroutinefunction(self)

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

    __repr__ = compose.__repr__
    __get__ = compose.__get__
    functions = compose.functions


class sacompose:
    """Sometimes-asynchronous function composition.

    sacompose(f, g)(...) is equivalent to:

        acompose(f, g)(...) if either f or g returns an awaitable object.
        compose(f, g)(...) if neither f nor g returns an awaitable object.
    """
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
            raise TypeError(_name(self) + '() needs at least one argument')
        _functions = []
        for function in reversed(functions):
            if not callable(function):
                raise TypeError(_name(self) + '() arguments must be callable')
            if (_iscoroutinefunction(function)
            or  _iscoroutinefunction(type(function).__call__)):
                _markcoroutinefunction(self)
            if isinstance(function, (acompose, sacompose)):
                _functions.extend(function.functions)
            else:
                _functions.append(function)
        self.__wrapped__ = _functions[0]
        self._wrappers = tuple(_functions[1:])

    def __call__(self, /, *args, **kwargs):
        """Call the composed function.

        The return value will either be a normal value if all composed
        callables return normal values, or an awaitable that needs an
        `await` if at least one composed callable returns an awaitable.
        """
        result = self.__wrapped__(*args, **kwargs)
        if _isawaitable(result):
            return _finish(self._wrappers, result)
        wrappers = iter(self._wrappers)
        for function in wrappers:
            result = function(result)
            if _isawaitable(result):
                return _finish(wrappers, result)
        return result

    __repr__ = compose.__repr__
    __get__ = compose.__get__
    functions = compose.functions


async def _finish(remaining_functions, first_awaitable_result):
    result = await first_awaitable_result
    for function in remaining_functions:
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
    sacompose.__name__ = 'sacompose'
