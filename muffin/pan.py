from collections import namedtuple
from functools import wraps

from pretty import pretty

from muffin.utensils import compose, curry_first, kleene


fs = frozenset


class Recursion(Exception):
    """
    Yo dawg.
    """


def key(args, kwargs):
    return args, fs(kwargs.iteritems())


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


def attempt(value):
    if isinstance(value, Lazy) and value.value is not None:
        value = value.value
    return value


def could_be_lazy(value):
    """
    Conservative laziness check.
    """

    return isinstance(value, (Lazy, Alt, Cat, Rep))


def lazyd(*args):
    """
    Lazily compute a derivative

    Only makes lazy objects if the arguments need to be lazily handled.
    """

    if any(could_be_lazy(arg) for arg in args):
        return Lazy(derivative, *args)
    return derivative(*args)


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

    def empty(self, f):
        return True

    def nullable(self, f):
        return False

    def only_null(self, f):
        return False

    def trees(self, f):
        return fs()


Empty = Empty("Empty")


class Null(Named, PrettyTuple):
    """
    The null string.
    """

    def derivative(self, c):
        return Empty

    def empty(self, f):
        return False

    def nullable(self, f):
        return True

    def only_null(self, f):
        return True

    def trees(self, f):
        return fs([None])


Null = Null("Null")


class Any(Named, PrettyTuple):
    """
    Any terminal.
    """

    def derivative(self, c):
        return Term(fs([c]))

    def empty(self, f):
        return False

    def nullable(self, f):
        return False

    def only_null(self, f):
        return False

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

    def empty(self, f):
        return False

    def nullable(self, f):
        return True

    def only_null(self, f):
        return True

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

    def empty(self, f):
        return False

    def nullable(self, f):
        return False

    def only_null(self, f):
        return False

    def trees(self, f):
        return fs()


class Set(PrettyTuple, namedtuple("Set", "s")):
    """
    Any member of a container of terminals.
    """

    def derivative(self, c):
        if c in self.s:
            return Term(fs([c]))
        else:
            return Empty

    def empty(self, f):
        return False

    def nullable(self, f):
        return False

    def only_null(self, f):
        return False

    def trees(self, f):
        return fs()


class Red(PrettyTuple, namedtuple("Red", "l, f")):
    """
    A reduction on languages.

    Yields a mapping of input data to output data when parsing.
    """

    def derivative(self, c):
        d = derivative(self.l, c)

        # We've got ways to just shut that whole thing down.
        if empty(d):
            return Empty

        # Eagerly apply the reduction right now.
        if only_null(d):
            return Term(fs(self.f(t) for t in trees(d)))

        # Compose reductions.
        if isinstance(d, Red):
            return Red(d.l, compose(d.f, self.f))

        return Red(d, self.f)

    def empty(self, f):
        return f(self.l)

    def nullable(self, f):
        return f(self.l)

    def only_null(self, f):
        return f(self.l)

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
        # Do some eager compaction here. Doing the test for emptiness is fine;
        # at this point, we've been forced and we're gonna do a nullability
        # test anyway.
        if empty(self.first):
            return Empty
        # Not so much here, though.
        if self.second is Empty:
            return Empty

        fd = derivative(self.first, c)
        sd = lazyd(self.second, c)

        l = Cat(fd, self.second)

        # Add in the second part if the first part's nullable.
        if nullable(self.first):
            ts = trees(self.first)
            partial = Cat(Term(ts), sd)

            if only_null(self.first):
                if not ts:
                    partial = Red(sd, curry_first(None))
                elif len(ts) == 1:
                    partial = Red(sd, curry_first(list(ts)[0]))

            return Alt(l, partial)
        else:
            return l

    def empty(self, f):
        return any(f(l) for l in self)

    def nullable(self, f):
        return all(f(l) for l in self)

    def only_null(self, f):
        return all(f(l) for l in self)

    def trees(self, f):
        return fs((x, y) for x in f(self.first) for y in f(self.second))


class Alt(PrettyTuple, namedtuple("Alt", "first, second")):
    """
    Alternation or union of parsers.

    Yields all succeeding components when parsing.

    This object's fields must be lazy.
    """

    def derivative(self, c):
        # Do some compaction.
        fd = lazyd(self.first, c)
        sd = lazyd(self.second, c)

        if empty(self.first):
            return sd
        if empty(self.second):
            return fd

        if fd is Empty:
            return sd
        if sd is Empty:
            return fd

        return Alt(fd, sd)

    def empty(self, f):
        return all(f(l) for l in self)

    def nullable(self, f):
        return f(self.first) or f(self.second)

    def only_null(self, f):
        return all(f(l) for l in self)

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
        # Do some compaction.
        if self.l is Empty:
            return Empty

        def repeat(xy):
            x, y = xy
            if y is None:
                return (x,)
            return (x,) + y

        # Cat needs to be lazy here too, since the inner language might not
        # yet be forced. Remember that Rep is lazy too!
        return Red(Cat(lazyd(self.l, c), self), repeat)

    def empty(self, f):
        return f(self.l)

    def nullable(self, f):
        return True

    def only_null(self, f):
        return False

    def trees(self, f):
        return fs([None])


@memo
def derivative(l, c):
    return force(l).derivative(c)


@kleene(True)
def empty(f):
    def inner(l):
        return force(l).empty(f)
    return inner


@kleene(False)
def nullable(f):
    def inner(l):
        return force(l).nullable(f)
    return inner


@kleene(True)
def only_null(f):
    def inner(l):
        return force(l).only_null(f)
    return inner


@kleene(fs())
def trees(f):
    def inner(l):
        return force(l).trees(f)
    return inner


@kleene(0)
def length(f):
    def inner(l):
        try:
            return sum(f(x) for x in force(l)) + 1
        except TypeError:
            return 1
    return inner


def cd(l, c):
    print "~ Derivative for", repr(c)
    d = derivative(l, c)
    # print d
    print "~ Size:", length(d)
    return d


def parses(l, s):
    for c in s:
        l = cd(l, c)
    return trees(l)


def matches(l, s):
    for c in s:
        l = cd(l, c)
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
