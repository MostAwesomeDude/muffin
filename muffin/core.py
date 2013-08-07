from collections import namedtuple
from functools import wraps
from operator import or_

from pretty import pprint


class Recursion(Exception):
    """
    Yo dawg.
    """


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
    stack = []

    @wraps(f)
    def inner(*args, **kwargs):
        k = key(args, kwargs)
        if k in cache:
            v = cache[k]
        elif k in stack:
            raise Recursion()
        else:
            try:
                stack.append(k)
                v = f(*args, **kwargs)
                cache[k] = v
            finally:
                stack.pop()
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

    return isinstance(value, (Lazy, Alt, Cat, Rep))


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

    def nullable(self, f):
        return False

    def compact(self):
        return self

    def trees(self, f):
        return frozenset()


Empty = Empty("Empty")


class Any(Named, PrettyTuple):
    """
    Any terminal.
    """

    def derivative(self, c):
        return Null(frozenset([c]))

    def nullable(self, f):
        return False

    def compact(self):
        return self

    def trees(self, f):
        return frozenset()


Any = Any("Any")


class Null(namedtuple("Null", "ts"), PrettyTuple):
    """
    The null set, representing a match with the null string.

    Yields terminals when parsing.
    """

    def derivative(self, c):
        return Empty

    def nullable(self, f):
        return True

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

    def nullable(self, f):
        return False

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

    def nullable(self, f):
        return f(self.l)

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
        l = Cat(lazy(derivative, self.first, c), self.second)

        if nullable(self.first):
            return Alt((l, lazy(derivative, self.second, c)))
        else:
            return l

    def nullable(self, f):
        return all(f(l) for l in self)

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
        return Cat(compact(self.first), compact(self.second))

    def trees(self, f):
        return set((x, y) for x in f(self.first) for y in f(self.second))


class Alt(namedtuple("Alt", "ls"), PrettyTuple):
    """
    Alternation or union of parsers.

    Yields all succeeding components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        return Alt(tuple(lazy(derivative, l, c) for l in self.ls))

    def nullable(self, f):
        return any(f(l) for l in self.ls)

    def compact(self):
        ls = [compact(l) for l in self.ls if l is not Empty]
        if len(ls) == 0:
            return Empty
        elif len(ls) == 1:
            return ls[0]
        else:
            new = []
            for l in ls:
                if isinstance(l, Alt):
                    for alt in l.ls:
                        new.append(alt)
                else:
                    new.append(l)
            return Alt(tuple(new))

    def trees(self, f):
        return reduce(or_, map(f, self.ls))

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
        return Red(Cat(lazy(derivative, self.l, c), self), tuple)

    def nullable(self, f):
        return True

    def compact(self):
        if self.l is Empty:
            return Null(frozenset())
        return Rep(compact(self.l))

    def trees(self, f):
        return frozenset()


def const(x):
    return x


@memo
def derivative(l, c):
    return force(l).derivative(c)


@memo
def compact(l):
    try:
        return force(l).compact()
    except Recursion:
        return l


@kleene(False)
def nullable(f):
    def inner(l):
        return force(l).nullable(f)
    return inner


@kleene(frozenset())
def trees(f):
    def inner(l):
        return force(l).trees(f)
    return inner


def parses(l, s):
    for c in s:
        l = compact(derivative(l, c))
    return trees(l)


def matches(l, s):
    for c in s:
        l = compact(derivative(l, c))
    return nullable(l)


def patch(lazy, obj):
    f, args = lazy._thunk
    if Patch in args:
        lazy.value = obj


def tie(obj):
    s = [obj]
    while s:
        node = s.pop()
        if not isinstance(node, (Cat, Alt, Rep)):
            continue
        for item in node:
            if isinstance(item, Lazy):
                patch(item, obj)
            elif isinstance(item, list):
                for thing in item:
                    s.append(thing)
            elif item is not obj:
                s.append(item)
