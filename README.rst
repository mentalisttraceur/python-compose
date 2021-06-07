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

This ``compose`` also fails fast with a ``TypeError`` if any
argument is not callable, or when called with no arguments.

This module also provides an ``acompose`` which can
compose both regular and ``async`` functions.


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
    >>> times_16 = compose(douple, double, double, double)

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

We can do all of the above with ``async`` functions
mixed in by using ``acompose`` instead of ``compose``:

.. code:: python

    from compose import acompose


Recipes
-------

* If you want composing zero functions to be the identity function:

  .. code:: python

      def identity(x):
          return x

      icompose = partial(compose, identity)

* If you want the ``functions`` attribute to be cached:

  .. code:: python

      import functools

      class ccompose(compose):
          @functools.cache_property
          def functions(self):
              return super().functions

* Compose arguments in opposite order (useful with things like
  ``functools.partial``, or just more intuitive in some cases):

  .. code:: python

      def rcompose(*functions):
          return compose(*reversed(functions))

* When you need a regular function instead of a callable class instance
  (for example, when you want to define a method using ``compose``):

  .. code:: python

      def fcompose(*functions):
          composed = compose(*functions)
          return lambda *args, **kwargs: composed(*args, **kwargs)
