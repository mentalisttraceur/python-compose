compose
=======

The classic ``compose``, with all the Pythonic features.

This ``compose`` follows the lead of ``functools.partial``
and returns callable ``compose`` objects which:

* have a regular and unambiguous ``repr``,
* retain correct signature introspection,
* allow introspection of the composed callables,
* can be type-checked,
* can be weakly referenced,
* can have attributes,
* will merge when nested, and
* can be pickled (if all composed callables can be pickled).

For ``async``/``await`` support, different variants of
``compose`` are included.


Versioning
----------

This library's version numbers follow the `SemVer 2.0.0
specification <https://semver.org/spec/v2.0.0.html>`_.


Installation
------------

::

    pip install compose

For static type checking, also install `the type hint
stubs <https://pypi.org/project/compose-stubs>`_:

::

    pip install compose-stubs


Usage
-----

Basics
~~~~~~

Import ``compose``:

.. code:: python

    >>> from compose import compose

All the usual function composition you know and love:

.. code:: python

    >>> def double(x):
    ...     return x * 2
    ...
    >>> def increment(x):
    ...     return x + 1
    ...
    >>> double_then_increment = compose(increment, double)
    >>> double_then_increment(1)
    3

Of course any number of functions can be composed:

.. code:: python

    >>> def double(x):
    ...     return x * 2
    ...
    >>> times_eight = compose(double, double, double)
    >>> times_16 = compose(double, double, double, double)

We still get the correct signature introspection:

.. code:: python

    >>> def f(a, b, c=0, **kwargs):
    ...     pass
    ...
    >>> def g(x):
    ...     pass
    ...
    >>> g_of_f = compose(g, f)
    >>> import inspect
    >>> inspect.signature(g_of_f)
    <Signature (a, b, c=0, **kwargs)>

And we can inspect all the composed callables:

.. code:: python

    >>> g_of_f.functions  # in order of execution:
    (<function f at 0x...>, <function g at 0x...>)

``compose`` instances flatten when nested:

.. code:: python

   >>> times_eight_times_two = compose(double, times_eight)
   >>> times_eight_times_two.functions == times_16.functions
   True

When programmatically inspecting arbitrary callables, we
can check if we are looking at a ``compose`` instance:

.. code:: python

    >>> isinstance(g_of_f, compose)
    True

``compose`` raises a ``TypeError`` when called with
no arguments or with any non-callable arguments:

.. code:: python

    >>> compose()
    Traceback (most recent call last):
        ...
    TypeError: compose() needs at least one argument

.. code:: python

    >>> compose(increment, 'oops', increment)
    Traceback (most recent call last):
        ...
    TypeError: compose() arguments must be callable


``async``/``await``
~~~~~~~~~~~~~~~~~~~

We can compose ``async`` code by using ``acompose``:

.. code:: python

    >>> import asyncio
    >>> from compose import acompose
    >>>
    >>> async def get_data():
    ...     # pretend this data is fetched from some async API
    ...     await asyncio.sleep(0)
    ...     return 42
    ...
    >>> get_and_double_data = acompose(double, get_data)
    >>> asyncio.run(get_and_double_data())
    84

``acompose`` can compose any number of ``async``
and regular functions, in any order:

.. code:: python

    >>> async def async_double(x):
    ...     await asyncio.sleep(0)
    ...     return x * 2
    ...
    >>> async_times_16 = acompose(async_double, double, async_double, double)
    >>> asyncio.run(async_times_16(1))
    16

``acompose`` instances always return awaitable values,
even if none of the composed functions are ``async``:

.. code:: python

    >>> awaitable_times_16 = acompose(double, double, double, double)
    >>> asyncio.run(async_times_16(1))
    16

``sacompose`` is like ``acompose``, but ``sacompose``
instances return an awaitable value only if any of
the composed functions return an awaitable value:

.. code:: python

    >>> from compose import sacompose
    >>>
    >>> regular_times_4 = sacompose(double, double)
    >>> awaitable_times_4 = sacompose(double, async_double)
    >>>    
    >>> regular_times_4(1)
    4
    >>> asyncio.run(awaitable_times_4(1))
    4

``acompose`` and ``sacompose`` instances flatten when nested:

.. code:: python

    >>> acompose(f, acompose(f, f)).functions == (f, f, f)
    True
    >>> acompose(sacompose(f, f), f).functions == (f, f, f)
    True
    >>> sacompose(acompose(f, f), f).functions == (f, f, f)
    True
    >>> sacompose(f, sacompose(f, f)).functions == (f, f, f)
    True

But ``compose`` instances *don't* flatten when nested 
into ``acompose`` and ``sacompose``, and vice versa:

.. code:: python

    >>> acompose(g_of_f).functions
    (compose(<function g at 0x...>, <function f at 0x...>),)
    >>> sacompose(g_of_f).functions
    (compose(<function g at 0x...>, <function f at 0x...>),)
    >>> compose(acompose(g, f)).functions
    (acompose(<function g at 0x...>, <function f at 0x...>),)
    >>> compose(sacompose(g, f)).functions
    (sacompose(<function g at 0x...>, <function f at 0x...>),)

``compose``, ``acompose``, and ``sacompose``
instances are all distinct types:

.. code:: python

    >>> isinstance(g_of_f, compose)
    True
    >>> isinstance(g_of_f, (acompose, sacompose))
    False
    >>> isinstance(async_times_16, acompose)
    True
    >>> isinstance(async_times_16, (compose, sacompose))
    False
    >>> isinstance(awaitable_times_4, sacompose)
    True
    >>> isinstance(awaitable_times_4, (compose, acompose))
    False
