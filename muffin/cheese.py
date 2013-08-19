from muffin.pan import matches, parses, tie, Alt, Cat, Ex, Lazy, Null, Patch
from muffin.utensils import const

S = Alt(Ex("N"), Cat(Lazy(const, Patch), Cat(Ex("+"), Lazy(const, Patch))))
tie(S)


def runS():
    s = "N" + "+N" * 10
    print matches(S, s)


B = Alt(Null,
        Cat(Lazy(const, Patch), Cat(Ex("("), Cat(Lazy(const, Patch),
            Ex(")")))))
tie(B)


def runB():
    s = "(())(())"
    print matches(B, s)
    print parses(B, s)
    s = "(((())))"
    print matches(B, s)
    print parses(B, s)
