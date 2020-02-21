compose
=======

The classic ``compose``, with all the Pythonic features.

This ``compose`` follows the lead of ``functools.partial``
and returns callable ``compose`` objects which:

* have a regular and unambiguous ``repr``,
* retain correct signature introspection,
* allow introspection of the composed callables,
* can be type-checked,
* can still be weakly referenced and have attributes,
* will merge when nested, and
* can be pickled (if all composed callables can be pickled).

This `compose` also fails fast with a ``TypeError`` if any
argument is not callable, or when called with no arguments.


Versioning
----------

This library's version numbers follow the `SemVer 2.0.0 specification
<https://semver.org/spec/v2.0.0.html>`_.

The current version number is available in the variable ``__version__``,
as is normal for Python modules.


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


Design Decisions
----------------

* The result of ``compose`` should be a drop-in replacement to
  functions in as many code paths as possible. Therefore:

  * The real signature of the composed function (the signature
    of the "inner-most" function) is exposed in the standard
    Python way (by assigning that function in ``__wrapped__``).

  * Arbitrary attribute assignment (``__dict__``) should work,
    because Python allows people to do that to functions.

  * Weak references (``__weakref__``) are supported,
    because Python allows weakly referencing functions.

* Failing fast as much as possible because that is important
  to help debugging by keeping errors local to their causes.

* ``__wrapped__`` cannot be a ``@property`` because several
  functions in the standard library cannot handle that.

  As a minor point, "portability conservatism": it is safer
  to bet on the most conservative feature-set possible.

* Storing the first function separately from the rest allows
  ``__call__`` to be written more efficiently, simply, and clearly.

* Treating ``compose()`` without any arguments as an error, instead
  of as producing a no-op passthrough identity function, because:

  1. It avoids turning mistakes into silent misbehavior by default.

  2. It is the more flexible way: people can do

    .. code:: python
        compose = partial(compose, identity)

    but going the other way is less trivial.

* Despite ``compose()`` being an error, ``__init__(self, *functions)__``
  is used instead of ``__init__(self, function, *functions)__``
  to produce a reliably nice and clear error message for that error.

* Using ``functools.recursive_repr`` if available because if recursion
  somehow ever happens, having a working and recursion-safe ``__repr__``
  would likely be extremely helpful for debugging and code robustness.

  Not going beyond that because the code involved would be complex and
  not portable across Python implementations and the right place for
  that is a separate polyfil, monkey-patched or added in manually.

* Manually getting ``self`` from ``*args`` in ``__call__``
  portably makes ``self`` a positional-only argument.

  If the user makes a typo, ``**``-splats arguments, or otherwise
  ends up passing ``self`` in ``kwargs``, maybe even intentionally,
  function composition should still work correctly - in this case,
  silent seemingly-successful unintended misbehavior would be awful.

  This is the same care we see taken in the
  implementation of ``functools.partial``.

* Not using ``__slots__`` because:

  1. ``__wrapped__`` cannot be in ``__slots__`` because that has
    the same problem as making it a ``@property`` (see above).

  2. ``__wrapped__`` can be implemented with ``__getattr__``,
    but this would cause an inconsistent error string or traceback
    when trying to get non-existent attributes relative to other
    typical objects, and did not seem to actually perform better.

  3. Due to ``__wrapped__``, ``__dict__`` will always be created
    and initialized in ``__init__``, so it would not save space.

  4. In my tests, using ``__slots__`` did not even produce
    reliably better runtimes than the regular version.
