from collections import namedtuple
from functools import wraps

from pretty import pprint


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


def memo(f):
    cache = {}

    @wraps(f)
    def inner(*args, **kwargs):
        k = key(args, kwargs)
        if k in cache:
            v = cache[k]
        else:
            v = f(*args, **kwargs)
            cache[k] = v
        return v
    return inner


class Named(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __pretty__(self, p, cycle):
        p.text(self.name)


class Lazy(object):
    value = None

    def __init__(self, f, *args):
        self._thunk = f, args

    def __repr__(self):
        if self.value is None:
            return "%r(%r)" % self._thunk
        else:
            return repr(self.value)

    def __hash__(self):
        # Hash the only thing that is constant and hashable on this class.
        return hash(id(self))

    def __pretty__(self, p, cycle):
        if self.value is not None:
            p.pretty(self.value)
            return

        if cycle:
            p.text("Lazy(...)")
            return

        p.text("Lazy(")
        p.text(self._thunk[0].__name__)
        p.text(",")
        p.breakable()
        p.pretty(self._thunk[1])
        p.text(")")

    def force(self):
        if self.value is None:
            f, args = self._thunk
            self.value = f(*args)


def nt(*args):
    """
    Hax namedtuples.
    """

    def f(self, p, cycle):
        name = type(self).__name__,
        if cycle:
            p.text("%s(...)" % name)
            return

        with p.group(1, "%s(" % name, ")"):
            for i, field in enumerate(self._fields):
                val = getattr(self, field)
                if i:
                    p.text(",")
                    p.breakable()
                p.text("%s=" % field)
                p.pretty(val)

    cls = namedtuple(*args)
    cls.__pretty__ = f
    return cls


def force(value):
    while isinstance(value, Lazy):
        value.force()
        value = value.value
    return value


Patch = Named("Patch")
Empty = Named("Empty")
Null = nt("Null", "ts")
Exactly = nt("Exactly", "x")
Red = nt("Red", "l, f")
Cat = nt("Cat", "first, second")
Alt = nt("Alt", "first, second")
Rep = nt("Rep", "l")
Delta = nt("Delta", "l")


def const(x):
    return x


@memo
def derivative(l, c):
    l = force(l)
    if l is Empty or isinstance(l, Null) or isinstance(l, Delta):
        return Empty
    elif isinstance(l, Exactly):
        if l.x == c:
            return Null(frozenset([c]))
        else:
            return Empty
    elif isinstance(l, Cat):
        # Must be lazy.
        return Alt(
            Lazy(Cat, Lazy(derivative, l.first, c), Lazy(const, l.second)),
            Lazy(Cat, Lazy(Delta, l.first), Lazy(derivative, l.second, c)),
        )
    elif isinstance(l, Alt):
        # Must be lazy.
        return Alt(Lazy(derivative, l.first, c), Lazy(derivative, l.second, c))
    elif isinstance(l, Rep):
        return Red(Cat(derivative(l.l, c), l), lambda x: (x,))
    elif isinstance(l, Red):
        return Red(derivative(l.l, c), l.f)
    assert False, "Can't classify %r" % l


@memo
def compact(l):
    l = force(l)
    if isinstance(l, Cat):
        if Empty in l:
            return Empty
        if isinstance(l.first, Null):
            return Red(compact(l.second), lambda x: set([l.first.ts + x]))
        if isinstance(l.second, Null):
            return Red(compact(l.first), lambda x: set([x + l.second.ts]))
        # Must be lazy.
        return Cat(Lazy(compact, l.first), Lazy(compact, l.second))
    if isinstance(l, Alt):
        if l.first == Empty:
            return compact(l.second)
        elif l.second == Empty:
            return compact(l.first)
        # Must be lazy.
        return Alt(Lazy(compact, l.first), Lazy(compact, l.second))
    if isinstance(l, Rep):
        if l.x is Empty:
            return Null(frozenset())
        # Must be lazy.
        return Rep(Lazy(compact, l.l))
    if isinstance(l, Red):
        if isinstance(l.l, Null):
            return Null(frozenset([l.f(t) for t in l.l.ts]))
        return Red(compact(l.l), l.f)
    if isinstance(l, Delta):
        # Must be lazy.
        return Delta(Lazy(compact, l.l))
    return l


@kleene(set())
def trees(f):
    def inner(l):
        l = force(l)
        if l is Empty:
            return set()
        elif isinstance(l, Null):
            return l.ts
        elif isinstance(l, Delta):
            return f(l.l)
        elif isinstance(l, Exactly):
            return set()
        elif isinstance(l, Alt):
            return f(l.first) | f(l.second)
        elif isinstance(l, Cat):
            # Use a genexp to not waste too much space.
            return set((x, y) for x in f(l.first) for y in f(l.second))
        elif isinstance(l, Red):
            # Same idea here.
            return set(l.f(x) for x in f(l.l))
        elif isinstance(l, Rep):
            return set()
        assert False, "Can't classify %r" % l
    return inner


def parses(l, s):
    for c in s:
        l = compact(derivative(l, c))
        pprint(l)
    return trees(l)


def matches(l, s):
    return bool(parses(l, s))


def patch(lazy, obj):
    f, args = lazy._thunk
    if args[0] is Patch:
        args = obj,
        lazy._thunk = f, args


def tie(obj):
    s = [obj]
    while s:
        node = s.pop()
        if not isinstance(node, (Cat, Alt, Rep, Delta)):
            continue
        for item in node:
            if isinstance(item, Lazy):
                patch(item, obj)
            elif item is not obj:
                s.append(item)
