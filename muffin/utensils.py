def const(x):
    return x


def compose(f, g):
    def h(x):
        return g(f(x))
    h.__name__ = "compose(%s, %s)" % (f.__name__, g.__name__)
    return h


def curry_first(x):
    def first(y):
        return x, y
    return first


def curry_second(x):
    def second(y):
        return y, x
    return second


def key(args, kwargs):
    return args, frozenset(kwargs.iteritems())


def kleene(bottom):
    """
    Kleene's fixed point.

    Ascend from a bottom value to a recursively-defined value. Usage is
    similar to a general fixed-point combinator, like U, Y, or Z, but with
    memoization and an explicit bottom value. This decorator can thus be used
    to deal with ill-founded recursion, as long as the values involved are
    sufficiently pure; if this decorator sees a value twice under the same
    circumstances, it will "bottom out" and ensure that the computation
    terminates eventually.
    """

    def first(f):
        cache = {}

        def second(x):
            def z(*args, **kwargs):
                k = key(args, kwargs)
                if k in cache:
                    v = cache[k]
                else:
                    cache[k] = bottom
                    v = x(x)(*args, **kwargs)
                    cache[k] = v
                return v
            return f(z)
        return second(second)
    return first


def once(f):
    cache = [None]
    def once(self, g):
        if cache[0] is None:
            cache[0] = f(self, g)
        return cache[0]
    return once
