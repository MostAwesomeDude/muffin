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


def force(value):
    while isinstance(value, Lazy):
        value.force()
        value = value.value
    return value


def could_be_lazy(value):
    """
    Conservative laziness check.
    """

    return isinstance(value, (Lazy, Alt, Cat, Delta, Rep))


def lazy(f, *args):
    """
    Make a lazy object if necessary.

    Only makes lazy objects if the arguments need to be lazily handled.
    """

    if any(could_be_lazy(arg) for arg in args):
        return Lazy(f, *args)
    return f(*args)


class PrettyTuple(object):

    def __pretty__(self, p, cycle):
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


Patch = Named("Patch")


class Empty(Named, PrettyTuple):
    """
    The empty set.
    """

    def derivative(self, c):
        return self

    def compact(self):
        return self

    def trees(self, f):
        return frozenset()


Empty = Empty("Empty")


class Null(namedtuple("Null", "ts"), PrettyTuple):
    """
    The null set, representing a match with the null string.

    Yields terminals when parsing.
    """

    def derivative(self, c):
        return Empty

    def compact(self):
        return self

    def trees(self, f):
        return self.ts


class Exactly(namedtuple("Exactly", "c"), PrettyTuple):
    """
    Exactly a single terminal.
    """

    def derivative(self, c):
        if self.c == c:
            return Null(frozenset([c]))
        else:
            return Empty

    def compact(self):
        return self

    def trees(self, f):
        return frozenset()


class Red(namedtuple("Red", "l, f"), PrettyTuple):
    """
    A reduction on languages.

    Yields a mapping of input data to output data when parsing.
    """

    def derivative(self, c):
        return Red(derivative(self.l, c), self.f)

    def compact(self):
        if isinstance(self.l, Null):
            return Null(frozenset(self.f(t) for t in self.l.ts))
        return Red(compact(self.l), self.f)

    def trees(self, f):
        return frozenset(self.f(x) for x in f(self.l))


class Cat(namedtuple("Cat", "first, second"), PrettyTuple):
    """
    Concatenation of parsers.

    Yields the product of its components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        return Alt(
            lazy(Cat,
                 lazy(derivative, self.first, c),
                 lazy(const, self.second)),
            lazy(Cat,
                 lazy(Delta, self.first),
                 lazy(derivative, self.second, c)),
        )

    def compact(self):
        if Empty in self:
            return Empty
        if isinstance(self.first, Null):
            ts = self.first.ts
            def f(x):
                return frozenset((t, x) for t in ts)
            return Red(compact(self.second), f)
        if isinstance(self.second, Null):
            ts = self.second.ts
            def g(x):
                return frozenset((x, t) for t in ts)
            return Red(compact(self.first), g)
        return Cat(lazy(compact, self.first), lazy(compact, self.second))

    def trees(self, f):
        return set((x, y) for x in f(self.first) for y in f(self.second))


class Alt(namedtuple("Alt", "first, second"), PrettyTuple):
    """
    Alternation or union of parsers.

    Yields all succeeding components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        return Alt(lazy(derivative, self.first, c), lazy(derivative, self.second, c))

    def compact(self):
        if self.first == Empty:
            return compact(self.second)
        elif self.second == Empty:
            return compact(self.first)
        return Alt(lazy(compact, self.first), lazy(compact, self.second))

    def trees(self, f):
        return f(self.first) | f(self.second)

class Rep(namedtuple("Rep", "l"), PrettyTuple):
    """
    Kleene star of a parser.

    Parses all repetitions, but only yields the least repetition when emitting
    final parse trees.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        # Cat needs to be lazy here too, since the inner language might not
        # yet be forced. Remember that Rep is lazy too!
        return Red(Cat(lazy(derivative, self.l, c), self), lambda x: (x,))

    def compact(self):
        if self.x is Empty:
            return Null(frozenset())
        # Must be lazy.
        return Rep(lazy(compact, self.l))

    def trees(self, f):
        return frozenset()


class Delta(namedtuple("Delta", "l"), PrettyTuple):
    """
    A parser which is null if its component parses null, and empty otherwise.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        return Empty

    def compact(self):
        return Delta(lazy(compact, self.l))

    def trees(self, f):
        return f(self.l)


def const(x):
    return x


@memo
def derivative(l, c):
    return force(l).derivative(c)


@memo
def compact(l):
    return force(l).compact()


@kleene(set())
def trees(f):
    def inner(l):
        return force(l).trees(f)
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
