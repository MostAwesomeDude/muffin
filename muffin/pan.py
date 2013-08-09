from collections import namedtuple
from functools import wraps
from operator import or_

from pretty import pretty

from muffin.utensils import compose


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
        return fs()


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


class Exactly(PrettyTuple, namedtuple("Exactly", "c")):
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
        return fs(self.f(x) for x in f(self.l))


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
            return Alt((l, partial))
        else:
            return l

    def nullable(self, f):
        return all(f(l) for l in self)

    def compact(self):
        if Empty in self:
            return Empty
        if isinstance(self.first, Term):
            ts = self.first.ts
            def f(x):
                return fs((t, x) for t in ts)
            return Red(compact(self.second), f)
        if isinstance(self.second, Term):
            ts = self.second.ts
            def g(x):
                return fs((x, t) for t in ts)
            return Red(compact(self.first), g)
        return Cat(compact(self.first), compact(self.second))

    def trees(self, f):
        return fs((x, y) for x in f(self.first) for y in f(self.second))


class Alt(PrettyTuple, namedtuple("Alt", "ls")):
    """
    Alternation or union of parsers.

    Yields all succeeding components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        return Alt(fs(lazy(derivative, l, c) for l in self.ls))

    def nullable(self, f):
        return any(f(l) for l in self.ls)

    def compact(self):
        ls = [compact(l) for l in self.ls if l is not Empty]
        if len(ls) == 0:
            return Empty
        elif len(ls) == 1:
            return ls[0]
        else:
            new = set()
            for l in ls:
                if isinstance(l, Alt):
                    for alt in l.ls:
                        new.add(alt)
                else:
                    new.add(l)
            return Alt(fs(new))

    def trees(self, f):
        return reduce(or_, map(f, self.ls))

class Rep(PrettyTuple, namedtuple("Rep", "l")):
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
            return Term(fs())
        return Rep(compact(self.l))

    def trees(self, f):
        return fs()


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


@kleene(fs())
def trees(f):
    def inner(l):
        return force(l).trees(f)
    return inner


def parses(l, s):
    for c in s:
        l = compact(derivative(l, c))
        print l
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
            elif isinstance(item, fs):
                for thing in item:
                    s.append(thing)
            elif item is not obj:
                s.append(item)
