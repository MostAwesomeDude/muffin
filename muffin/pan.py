from collections import namedtuple
from functools import wraps

from pretty import pretty

from muffin.utensils import compose, const, curry_first, curry_second


fs = frozenset


class Recursion(Exception):
    """
    Yo dawg.
    """


def key(args, kwargs):
    return args, fs(kwargs.iteritems())


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

    __repr__ = pretty

    def __pretty__(self, p, cycle):
        p.text(self.name)


class Lazy(object):
    value = None

    def __init__(self, f, *args):
        self._thunk = f, args

    __repr__ = pretty

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

    __repr__ = pretty

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
        return fs()


Empty = Empty("Empty")


class Null(Named, PrettyTuple):
    """
    The null string.
    """

    def derivative(self, c):
        return Empty

    def nullable(self, f):
        return True

    def compact(self):
        return self

    def trees(self, f):
        return fs([None])


Null = Null("Null")


class Any(Named, PrettyTuple):
    """
    Any terminal.
    """

    def derivative(self, c):
        return Term(fs([c]))

    def nullable(self, f):
        return False

    def compact(self):
        return self

    def trees(self, f):
        return fs()


Any = Any("Any")


class Term(PrettyTuple, namedtuple("Term", "ts")):
    """
    A nullable node which has matched a terminal.

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


class Ex(PrettyTuple, namedtuple("Ex", "c")):
    """
    Exactly a single terminal.
    """

    def derivative(self, c):
        if self.c == c:
            return Term(fs([c]))
        else:
            return Empty

    def nullable(self, f):
        return False

    def compact(self):
        return self

    def trees(self, f):
        return fs()


class Red(PrettyTuple, namedtuple("Red", "l, f")):
    """
    A reduction on languages.

    Yields a mapping of input data to output data when parsing.
    """

    def derivative(self, c):
        return Red(derivative(self.l, c), self.f)

    def nullable(self, f):
        return f(self.l)

    def compact(self):
        if isinstance(self.l, Term):
            return Term(fs(self.f(t) for t in self.l.ts))
        elif isinstance(self.l, Red):
            return Red(compact(self.l.l), compose(self.l.f, self.f))
        return Red(compact(self.l), self.f)

    def trees(self, f):
        ts = f(self.l)
        return fs(map(self.f, ts))


class Cat(PrettyTuple, namedtuple("Cat", "first, second")):
    """
    Concatenation of parsers.

    Yields the product of its components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        l = Cat(lazy(derivative, self.first, c), self.second)

        if nullable(self.first):
            terms = Term(trees(self.first))
            partial = Cat(terms, lazy(derivative, self.second, c))
            return Alt(l, partial)
        else:
            return l

    def nullable(self, f):
        return all(f(l) for l in self)

    def compact(self):
        if Empty in self:
            return Empty

        first = compact(self.first)
        second = compact(self.second)

        if isinstance(self.first, Term):
            ts = self.first.ts
            if not ts:
                return Red(second, curry_first(None))
            elif len(ts) == 1:
                return Red(second, curry_first(list(ts)[0]))
        if isinstance(self.second, Term):
            ts = self.second.ts
            if not ts:
                return Red(first, curry_second(None))
            elif len(ts) == 1:
                return Red(first, curry_second(list(ts)[0]))
        return Cat(first, second)

    def trees(self, f):
        return fs((x, y) for x in f(self.first) for y in f(self.second))


class Alt(PrettyTuple, namedtuple("Alt", "first, second")):
    """
    Alternation or union of parsers.

    Yields all succeeding components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        return Alt(lazy(derivative, self.first, c),
                   lazy(derivative, self.second, c))

    def nullable(self, f):
        return self.first.nullable(f) or self.second.nullable(f)

    def compact(self):
        first = compact(self.first)
        second = compact(self.second)
        if first is Empty:
            return second
        elif second is Empty:
            return first
        else:
            return Alt(first, second)

    def trees(self, f):
        return f(self.first) | f(self.second)


class Rep(PrettyTuple, namedtuple("Rep", "l")):
    """
    Kleene star of a parser.

    Parses all repetitions, but only yields the least repetition when emitting
    final parse trees.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        def repeat(xy):
            x, y = xy
            if y is None:
                return (x,)
            return (x,) + y

        # Cat needs to be lazy here too, since the inner language might not
        # yet be forced. Remember that Rep is lazy too!
        return Red(Cat(lazy(derivative, self.l, c), self), repeat)

    def nullable(self, f):
        return True

    def compact(self):
        if self.l is Empty:
            return Term(fs())
        return Rep(compact(self.l))

    def trees(self, f):
        return fs([None])


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


@kleene(fs())
def trees(f):
    def inner(l):
        return force(l).trees(f)
    return inner


def cd(l, c):
    d = derivative(l, c)
    print "WRT", c, ":", d
    l = compact(d)
    print "Compacted:", l
    return l


def parses(l, s):
    print
    print "Initial:", l
    for c in s:
        l = cd(l, c)
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
            elif item is not obj:
                s.append(item)
