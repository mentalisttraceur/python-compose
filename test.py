from compose import compose


def test_compose():
    def f(s):
        return s + 'f'
    def g(s):
        return s + 'g'
    f_g = compose(f, g)
    assert f_g('') == 'gf'  # Remember that it's f(g(...)) so g runs first
    assert f_g.functions == (g, f)  # functions exposed in execution order


def test_inlining():
    def f(_):
        return None
    f_f = compose(f, f)
    f_f_f = compose(f_f, f)
    assert f_f_f.functions == (f, f, f)


def test_reject_empty():
    try:
        compose()
    except TypeError:
        return
    assert False, 'compose() should have raised'


def _test_reject_non_callable(*args):
    try:
        compose(*args)
    except TypeError:
        return
    assert False, 'compose(..., None, ...) should have raised'


def test_reject_non_callable():
    def f(_):
        return None
    _test_reject_non_callable(None)
    _test_reject_non_callable(f, None)
    _test_reject_non_callable(None, f)
    _test_reject_non_callable(None, None)
    _test_reject_non_callable(f, None, f)
    _test_reject_non_callable(None, f, None)


def test_pickle():
    import pickle

    # `pickle.HIGHEST_PROTOCOL` was added in Python 2.3, but so was
    # `list.extend`, and the main code relies on that already.
    highest_protocol = pickle.HIGHEST_PROTOCOL
    protocol = 0

    compose_in_compose_instance = compose(compose)

    while protocol <= highest_protocol:
        pickle.loads(pickle.dumps(compose_in_compose_instance, protocol))
        protocol += 1
    # Finishing the loop without exception is a pass.


def test_repr_eval():
    class CallableWithEvaluatableRepr(object):
        def __repr__(self):
            return type(self).__name__ + '()'
        def __call__(self, *args, **kwargs):
            return None

    c = CallableWithEvaluatableRepr()

    c1 = compose(c)
    c2 = eval(repr(c1))
    assert repr(c1) == repr(c2), 'repr eval failed on compose(c)'

    c1 = compose(c, c)
    c2 = eval(repr(c1))
    assert repr(c1) == repr(c2), 'repr eval failed on compose(c, c)'

    c1 = compose(c, c, c)
    c2 = eval(repr(c1))
    assert repr(c1) == repr(c2), 'repr eval failed on compose(c, c, c)'
