from muffin.pan import matches, tie, Alt, Cat, Ex, Lazy, Patch
from muffin.utensils import const

S = Alt(Ex("N"), Cat(Lazy(const, Patch), Cat(Ex("+"), Lazy(const, Patch))))
tie(S)

def runS():
    s = "N" + "+N" * 10
    print matches(S, s)
