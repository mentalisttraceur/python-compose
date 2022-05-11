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

This ``compose`` also:

* fails fast with a ``TypeError`` if any argument is not
  callable, or when called with no arguments, and
* comes with an ``acompose`` variant which automatically
  does the right thing with ``async`` callables.


Versioning
----------

This library's version numbers follow the `SemVer 2.0.0
specification <https://semver.org/spec/v2.0.0.html>`_.


Installation
------------

::

    pip install compose


Usage
-----

Import ``compose``:

.. code:: python

    from compose import compose

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
    >>> times_eight = compose(douple, double, double)
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
    (<function f at 0x4048e6f0>, <function g at 0x405228e8>)

When programmatically inspecting arbitrary callables, we
can check if we are looking at a ``compose`` instance:

.. code:: python

    >>> isinstance(g_of_f, compose)
    True

We can compose ``async`` code by using ``acompose``:

.. code:: python

    >>> import asyncio
    >>> from compose import acompose
    >>>
    >>> async def get_data():
    ...     await asyncio.sleep(0)
    ...     return 42
    ...
    >>> get_and_double_data = acompose(double, get_data)
    >>> asyncio.run(get_and_double_data())
    84

Of course we can compose any number of ``async``
and regular functions, in any order:

.. code:: python

    >>> async def async_double(x):
    ...     await asyncio.sleep(0)
    ...     return x * 2
    ...
    >>> async_times_16 = acompose(async_double, double, async_double, double)
    >>> asyncio.run(async_times_16(1))
    16

``compose`` and ``acompose`` instances are distinct
types:

.. code:: python

    >>> isinstance(async_times_16, acompose)
    True
    >>> isinstance(async_times_16, compose)
    False
    >>> isinstance(g_of_f, acompose)
    False


Recipes
-------

* If you want composing zero functions to be the identity function:

  .. code:: python

      def identity(x):
          return x

      icompose = partial(compose, identity)

* To compose arguments in reverse order:

  .. code:: python

      def rcompose(*functions):
          return compose(*reversed(functions))

* When you need composition to return a regular Python function:

  .. code:: python

      def fcompose(*functions):
          composed = compose(*functions)
          return lambda *args, **kwargs: composed(*args, **kwargs)
