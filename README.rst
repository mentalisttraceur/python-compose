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

This ``compose`` also fails fast with a ``TypeError`` if any
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

  * The proper signature of the composed function is exposed
    in the standard Python way (by exposing the "inner-most"
    function as the attribute ``__wrapped__``).

  * Arbitrary attribute assignment (``__dict__``) should work,
    because Python allows people to do that to functions.

  * Weak references (``__weakref__``) are supported,
    because Python allows weakly referencing functions.

* Failing-fast as much as possible because that is important
  to help debugging by keeping errors local to their causes.

* Treating ``compose()`` with no arguments as an error, instead
  of as implicitly composing with an identity function, because:

  * It avoids turning mistakes into silent misbehavior by default.

  * People who want the other behavior can more trivially build
    it on top of this behavior than the other way around:

    .. code:: python

        compose = partial(compose, identity)

* Doing ``__init__(self, *functions)`` instead of
  ``__init__(self, function, *functions)`` because:

  * It makes the signature and docstring more correctly hint that the
    first function argument is not special or different from the rest.

  * It allows manually raising an error with a clearer and more
    helpful message if ``compose()`` is called with no arguments.

* Using ``functools.recursive_repr`` if available because if recursion
  happens, having a working and recursion-safe ``__repr__`` would
  likely be extremely helpful for debugging and code robustness.

  Not going beyond that because the code involved would be complex and
  not portable across Python implementations, and the right place to
  solve that is a separate polyfil if at all possible.

* ``self`` has to be a positional-only argument of ``__call__``
  to make ``__call__`` properly transparent in all cases.

  If the user makes a typo, ``**``-splats arguments, or otherwise
  ends up passing ``self`` in ``kwargs``, maybe even intentionally,
  function composition should still work correctly - in this case,
  silent seemingly-successful unintended misbehavior would be awful.

  If the user uses ``compose`` to implement methods, the ``self``
  argument to that method going through ``compose`` will normally
  be a positional argument, but ideally should be passed through
  transparently even if not, to match how normal methods work.

* Manually getting ``self`` from ``*args`` in ``__call__``
  **portably** makes ``self`` a positional-only argument.

* Optimization priorities are:

  1. "Optimize for optimization": implementing the essential logic
     of the intended behavior in as clearly and simply as possible,
     because that helps optimizers.

  2. ``__call__``, because that is the code path which can only be
     extracted from hot loops or other spots where performance
     matters by not using ``compose`` at all.

  3. ``__init__``, because composing callables together is also
     essential to actually using this, and in some cases cannot
     be pulled out of performance-sensitive code paths.

  4. Not storing data redundantly, because memory-constrained
     systems are a thing, and it is much easier to add redundant
     data on top of an implementation than it is to remove it.

* Flattening nested instances of ``compose`` because

  * ``__call__`` performance is more important in typical cases
    that runspace efficiency (see above performance priorities).

  * Intermediate composed functions that are never used
    after composing them with something else can just
    be deleted so that they don't take up memory.

  * It is more trivial to prevent the flattening by using a
    simple wrapper function or class on this implementation
    than flattening on top of a not-flattening one.

* Using tuples and a read-only ``@property`` for storing
  and exposing the composed functions because:

  * Immutability helps reasoning about and validating code.

  * Immutable types provide more optimisation opportunities
    that a Python implementation could take advantage of.

  * Discouraging mutations encourages optimizer-friendly code.

  * Mutability is normally not needed for composed functions.

  * ``functools.partial`` also only exposes read-only attributes.

  * Immutability now is forward-compatible with mutability later;
    changing mutability into immutability is a breaking change.

  * A simple mutable variant can be implemented trivially
    on top of the current immutable ``compose``:

    .. code:: python

        class compose(compose):
            def __init__(self, *functions):
                super(compose, self).__init__(*functions)
                self._wrappers = list(self._wrappers)

* Generating the ``functions`` attribute tuple every time instead
  of caching it, because:

  * This implementation prevents *accidental* inconsistencies
    if someone intentionally bypasses the immutability.

    (Intentional inconsistencies that can only be introduced *by
    deliberately modifying the implementation* are fine. What's
    important is minimizing the surface area for errors and
    debugging difficulty being introduced by merely *forgetting*
    or *not realizing* the need to keep things consistent.)

  * The performance priority of not storing data redundantly as
    part of composing and calling is usually more important
    than introspection performance, *especially* because the
    caching can be implemented much more trivially on top of
    this implementation than preventing caching would be if
    it was implemented in ``compose``.

  * A caching variant can be implemented on top
    of the current non-caching ``compose``:

    .. code:: python

        class compose(compose):
            @property
            def functions(self):
                try:
                    return self._functions
                except AttributeError:
                    pass
                self._functions = super(compose, self).functions
                return self._functions

* Storing the first function separately from the rest allows
  ``__call__`` to be more efficient, simpler, and clearer.

* ``__wrapped__`` cannot be a ``@property`` because several
  functions in the standard library cannot handle that.

  As a minor point, "portability conservatism": it is safer
  to bet on the most conservative feature-set possible.

* Not using ``__slots__`` because of many weak reasons adding up:

  * ``__call__`` performance is basically the same, at best
    only marginally better, when using ``__slots__``.

    (``__init__`` sees a better but still small improvement.)

  * ``__slots__`` forces more code to support older
    pickle protocols for those who might need that.

    (But one-liner ``__getstate__`` and ``__setstate__`` that
    just handle the 3-tuple of ``_wrapped``, ``_wrappers``,
    and ``__dict__`` would work, and are probably optimal.)

  * ``__wrapped__`` cannot be in ``__slots__`` because that has
    the same problem as making it a ``@property`` (see above).

  * ``__wrapped__`` can be implemented with ``__getattr__``
    redirecting to a slotted ``_wrapped``, although once
    upon a type Transcrypt didn't support ``__getattr__``,
    which is a great example for portability conservatism.

  * ``__wrapped__`` can be implemented with ``__getattribute__``
    redirecting to a slotted ``_wrapped``, but implementing the
    ``__getattribute__`` function is much slower than just not
    using ``__slots__`` at all, since it proxies all attribute
    access.

  * If ``__wrapped__`` is stored in ``__dict__`` and is always
    set in ``__init__``, a lot of the memory savings from
    using ``__slots__`` are negated.

* When flattening composed ``compose`` instances in ``__init__``,
  ``__wrapped__`` and ``_wrapped`` attributes are used instead
  of the ``functions`` attribute, because:

  * Speed of composition significantly increases, given
    that ``functions`` is generated every time.

  * The loss of symmetry between this and the public interface
    of the ``functions`` attribute is unfortunate, because it
    forces any subclasses to use ``_wrappers`` consistently
    with ``compose`` instead of just ``functions``, but the
    advantage seems to be worthwhile.

* The ``functions`` generation uses ``tuple(self._wrappers)``
  instead of just ``self._wrappers`` to enable subclasses
  that make ``_wrappers`` something other than a tuple to
  still work properly.

  A subclass which wants ``functions`` itself to be something
  other than a tuple would need to provide that themselves,
  but this should cover at least some cases.

  Importantly, because tuples are immutable, calling ``tuple``
  on a tuple just returns the same tuple instead of copying in
  CPython, and other Pythons can do that optimization too.

* Not providing a separate ``rcompose`` (which would compose
  its arguments in reverse order) for now, because it is
  trivial to implement on top of ``compose`` if needed:

  .. code:: python

      def rcompose(*functions):
          return compose(*reversed(functions))

* Not providing a separate "just a normal function" variant for now,
  because it is trivial to implement on top of ``compose`` if needed:

  .. code:: python

      def fcompose(*functions):
          composed = compose(*functions)
          return lambda *args, **kwargs: composed(*args, **kwargs)

* Not providing descriptor support like ``functools.partialmethod``
  for now, until a need for it becomes apparent which a "normal
  function" variant (see last point) does not satisfy well enough.
